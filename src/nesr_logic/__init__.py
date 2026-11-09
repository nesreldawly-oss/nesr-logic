"""NESR Logic: General-purpose Python Logic Discovery and Extraction."""
from __future__ import annotations

import ast
import dataclasses
import io
import json
import os
import pathlib
import re
import tokenize
from typing import Any

__version__ = "0.1.0"
__all__ = ["LogicRecord", "ScanReport", "scan", "scan_file", "format_report", "main"]

BIZ_KW = {"price", "cost", "tax", "discount", "total", "amount", "rate", "fee", "salary", "invoice", "payment", "balance", "limit", "order", "revenue", "budget"}
SEC_KW = {"role", "admin", "auth", "token", "secret", "permission", "password", "user", "access", "credential", "allow", "deny", "login"}
MATH_FNS = {"abs", "round", "min", "max", "sum", "pow", "sqrt", "ceil", "floor", "log", "exp"}
VAL_FNS = {"isinstance", "hasattr", "issubclass", "len", "callable"}


@dataclasses.dataclass
class LogicRecord:
    id: str
    category: list[str]
    description: str
    file: str
    line_start: int
    line_end: int
    expression: str
    inputs: list[str]
    outputs: list[str]
    inferred_types: dict[str, str]
    dependencies: list[str]
    is_annotated: bool
    detection_method: str
    confidence: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class ScanReport:
    target: str
    records: list[LogicRecord] = dataclasses.field(default_factory=list)
    errors: list[dict[str, str]] = dataclasses.field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "summary": self.summary(), "records": [r.to_dict() for r in self.records], "errors": self.errors}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> dict[str, Any]:
        cats: dict[str, int] = {}
        for r in self.records:
            for c in r.category: cats[c] = cats.get(c, 0) + 1
        return {"total_records": len(self.records), "explicit_annotated": sum(1 for r in self.records if r.is_annotated),
                "auto_detected": sum(1 for r in self.records if not r.is_annotated), "warnings_count": sum(len(r.warnings) for r in self.records),
                "categories": cats, "errors_count": len(self.errors)}

    def format_terminal(self) -> str:
        s = self.summary()
        lines = [f"=== NESR Logic Scan Report: {self.target} ===",
                 f"Total: {s['total_records']} (Annotated: {s['explicit_annotated']}, Auto: {s['auto_detected']}, Errors: {s['errors_count']})\n"]
        for r in self.records:
            tag = "[ANNOTATED]" if r.is_annotated else "[AUTO-DETECTED]"
            lines.append(f"{tag} {r.id} | {r.file}:{r.line_start}-{r.line_end} | {', '.join(r.category)}")
            lines.append(f"  Expr: {r.expression}\n  Inputs: {r.inputs} | Outputs: {r.outputs} | Types: {r.inferred_types} | Conf: {r.confidence}")
            lines.extend(f"  {w}" for w in r.warnings)
        lines.extend(f"[ERROR] {e['file']}: {e['message']}" for e in self.errors)
        return "\n".join(lines)


def format_report(report: ScanReport) -> str:
    return report.format_terminal()


def _find_annotations(code_bytes: bytes) -> set[int]:
    annot_lines, code_lines, pending_line = set(), set(), 0
    try:
        for t in tokenize.tokenize(io.BytesIO(code_bytes).readline):
            if t.type in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING, tokenize.OP):
                code_lines.add(t.start[0])
                if pending_line and t.start[0] == pending_line + 1:
                    annot_lines.add(t.start[0])
                pending_line = 0
            elif t.type == tokenize.COMMENT and re.search(r"#\s*\(L\)(?:\s*[:\-].*)?$", t.string.strip()):
                if t.start[0] in code_lines: annot_lines.add(t.start[0])
                else: pending_line = t.start[0]
    except tokenize.TokenError:
        pass
    return annot_lines


def _classify_and_extract(
    node: ast.AST, expr_node: ast.AST, code_lines: list[str],
    file_path: str, idx: int, is_annot: bool, outputs: list[str],
) -> LogicRecord:
    names, calls, idents, nodes = set(), set(), set(outputs), []
    for n in ast.walk(expr_node):
        nodes.append(n)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load): names.add(n.id); idents.add(n.id)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name): calls.add(n.func.id)
        elif isinstance(n, ast.Attribute): idents.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str): idents.add(n.value)

    has_cmp = any(isinstance(n, ast.Compare) for n in nodes)
    has_bool = any(isinstance(n, ast.BoolOp) for n in nodes)
    has_bin = any(isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)) for n in nodes)
    has_unary_not = any(isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not) for n in nodes)
    has_unary_arith = any(isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)) for n in nodes)
    has_if = isinstance(node, (ast.If, ast.While, ast.IfExp)) or any(isinstance(n, ast.IfExp) for n in nodes)
    has_assert = isinstance(node, ast.Assert)
    has_biz = any(any(k in s.lower() for k in BIZ_KW) for s in idents)
    has_sec = any(any(k in s.lower() for k in SEC_KW) for s in idents)

    cats = []
    if has_bin or has_unary_arith: cats.append("Arithmetic Logic")
    if has_bin or (calls & MATH_FNS): cats.append("Mathematical Logic")
    if has_bool or has_unary_not: cats.append("Boolean Logic")
    if has_if: cats.append("Conditional Logic")
    if has_biz: cats.append("Business Logic")
    if has_if or has_bool or (has_cmp and outputs): cats.append("Decision Logic")
    if has_cmp: cats.append("Relational Logic")
    if (has_cmp and any(len(getattr(n, "ops", [])) > 1 for n in nodes)) or has_assert or any(any(x in k for x in ("limit", "bound", "min", "max")) for k in idents):
        cats.append("Constraint Logic")
    if has_sec: cats.append("Security Logic")
    if has_assert or (calls & VAL_FNS) or (has_cmp and any(any(isinstance(c, ast.Constant) and c.value is None for c in n.comparators) for n in nodes if isinstance(n, ast.Compare))):
        cats.append("Validation Logic")
    if isinstance(node, (ast.If, ast.While)): cats.append("Control Logic")
    if not cats: cats.append("Unknown / Unclassified Logic")

    types = {out: "bool" for out in outputs} if (has_cmp or has_bool or has_unary_not) else \
            {out: ("float" if any(isinstance(n.op, ast.Div) for n in nodes if isinstance(n, ast.BinOp)) else "number") for out in outputs} if has_bin else {}
    if isinstance(node, ast.AnnAssign) and isinstance(node.annotation, ast.Name):
        for out in outputs: types[out] = node.annotation.id

    target_node = expr_node if isinstance(node, (ast.If, ast.While, ast.Assert)) else node
    start = getattr(target_node, "lineno", getattr(node, "lineno", 1))
    end = getattr(target_node, "end_lineno", start)
    expr_text = "\n".join(code_lines[start - 1:end]).strip()
    warnings = []
    if not is_annot:
        warnings.append(
            f"[WARNING] Potential unannotated logic detected\nFile: {file_path}\nLine: {start}\n"
            f"Category: {' / '.join(cats[:2])}\nSuggested action:\nReview this expression and consider adding (L)."
        )

    return LogicRecord(
        id=f"LOG-{idx:04d}", category=cats, description=f"{cats[0]} operation", file=file_path,
        line_start=start, line_end=end, expression=expr_text, inputs=sorted(names), outputs=outputs,
        inferred_types=types, dependencies=sorted(calls), is_annotated=is_annot,
        detection_method="explicit_annotation" if is_annot else "ast_heuristic",
        confidence="high" if is_annot else ("medium" if len(cats) > 1 else "low"), warnings=warnings,
    )


def scan_file(file_path: str | os.PathLike) -> ScanReport:
    p = pathlib.Path(file_path)
    report = ScanReport(target=str(p))
    try: raw = p.read_bytes()
    except Exception as e:
        report.errors.append({"file": str(p), "message": f"Read error: {e}"}); return report
    if not raw.strip(): return report
    try:
        source = raw.decode("utf-8")
        tree = ast.parse(source, filename=str(p))
    except Exception as e:
        report.errors.append({"file": str(p), "message": f"Syntax/Decode error: {e}"}); return report

    annot_lines, code_lines, records = _find_annotations(raw), source.splitlines(), []
    for stmt in ast.walk(tree):
        outputs, expr = [], None
        if isinstance(stmt, ast.Assign): outputs, expr = [t.id for t in stmt.targets if isinstance(t, ast.Name)], stmt.value
        elif isinstance(stmt, (ast.AnnAssign, ast.AugAssign)): outputs, expr = ([stmt.target.id] if isinstance(stmt.target, ast.Name) else []), stmt.value
        elif isinstance(stmt, (ast.If, ast.While, ast.Assert)): expr = stmt.test
        elif isinstance(stmt, (ast.Return, ast.Expr)): expr = stmt.value
        if expr is None: continue

        stmt_lines = set(range(stmt.lineno, getattr(stmt, "end_lineno", stmt.lineno) + 1))
        is_annot = bool(stmt_lines & annot_lines)
        has_logic = isinstance(stmt, (ast.If, ast.While, ast.Assert)) or any(isinstance(n, (ast.Compare, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp)) for n in ast.walk(expr))
        if not is_annot and (not has_logic or isinstance(expr, ast.Constant)): continue
        if not is_annot and isinstance(stmt, ast.Expr) and not any(isinstance(n, (ast.Compare, ast.BoolOp, ast.IfExp)) for n in ast.walk(expr)): continue
        records.append(_classify_and_extract(stmt, expr, code_lines, str(p), len(records) + 1, is_annot, outputs))

    report.records = sorted(records, key=lambda r: (r.line_start, r.id))
    return report


def scan(path: str | os.PathLike) -> ScanReport:
    p = pathlib.Path(path)
    if p.is_file(): return scan_file(p)
    combined = ScanReport(target=str(p))
    for root, _, files in os.walk(p):
        for f in sorted(files):
            if f.endswith(".py"):
                res = scan_file(pathlib.Path(root) / f)
                combined.records.extend(res.records)
                combined.errors.extend(res.errors)
    for i, r in enumerate(combined.records, 1): r.id = f"LOG-{i:04d}"
    return combined


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="nesr-logic", description="General-purpose Python Logic Discovery and Extraction")
    sub = parser.add_subparsers(dest="cmd")
    scan_p = sub.add_parser("scan", help="Scan Python files for logic")
    scan_p.add_argument("path", nargs="?", default=".", help="Path to file or directory")
    scan_p.add_argument("--json", action="store_true", help="Output JSON report")
    scan_p.add_argument("--strict", action="store_true", help="Exit 1 on warnings or errors")
    args = parser.parse_args(argv)
    if args.cmd != "scan":
        parser.print_help(); return 0
    rep = scan(args.path)
    print(rep.to_json() if args.json else rep.format_terminal())
    return 1 if (args.strict and (rep.errors or any(r.warnings for r in rep.records))) else 0
