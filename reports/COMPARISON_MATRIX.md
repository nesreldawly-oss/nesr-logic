# NESR Logic — Comparison Decision Matrix
**Audit Date**: 2026-11-09  
**Version**: 0.1.0

---

## Decision Classifications

| Label | Meaning |
|---|---|
| **KEEP** | Current approach is correct; no change needed |
| **IMPROVE** | Approach is valid but needs refinement without redesign |
| **REPLACE** | A clearly better alternative exists |
| **REMOVE** | Unnecessary complexity or dead weight |
| **DEFER** | Valuable but not needed for 0.1.0 |

---

## 1. Source Analysis Technology

| Area | Current Approach | Alternative | Current Advantages | Current Disadvantages | Recommendation |
|---|---|---|---|---|---|
| **AST parsing** | `ast.parse()` stdlib | LibCST, parso | Zero dependency, 100% stdlib, fast, well-documented | Lossy (drops comments, whitespace) | **KEEP** — Read-only analysis does not need lossless CST |
| **Comment detection** | `tokenize.tokenize()` stdlib | LibCST (has comment nodes) | Zero dependency; accurately finds `# (L)` without CST | Two-pass analysis required | **KEEP** — Tokenizer is the correct stdlib tool for comment access |
| **AST traversal** | `ast.walk()` (BFS, flat) | `ast.NodeVisitor` (DFS, context-aware) | Simple, fewer lines | No scope/context tracking; outer `if` captures whole block in expression text | **IMPROVE** — Migrate to `NodeVisitor` for 0.2.0; acceptable for 0.1.0 |
| **Inspect module** | Not used | `inspect` on live objects | n/a | Would require importing scanned files — safety violation | **KEEP NOT USED** |
| **Symbol table** | Not used | `symtable.symtable()` | n/a | Provides scope/binding info but requires separate stdlib import | **DEFER** — Useful for future data-flow analysis |
| **Third-party parsers** | Not used | LibCST, parso, astroid | n/a | Add external runtime dependencies | **DEFER** — Only add if lossless round-tripping or autofixing is needed |

---

## 2. Logic Detection Strategy

| Area | Current Approach | Alternative | Current Advantages | Current Disadvantages | Recommendation |
|---|---|---|---|---|---|
| **Detection method** | AST pattern matching + keyword heuristics | Rule-based visitor, data-flow analysis, ML classifiers | Simple, explainable, zero deps | No data-flow, no scope awareness | **KEEP** — Appropriate for stated scope and line budget |
| **Classification triggers** | Boolean feature flags (`has_cmp`, `has_bool`, etc.) | Scoring system, Prolog rules, decision trees | Simple, readable, testable | Category explosion (12 cats always evaluated simultaneously) | **KEEP** — Adequate; consider ordered priority for 0.2.0 |
| **Business logic detection** | Identifier keyword matching against `BIZ_KW` set | Domain-specific rules, ML intent classifiers | Zero deps, works without semantic understanding | High false-positive rate for ambiguous words like `order`, `limit` | **IMPROVE** — Narrow BIZ_KW; require both a logic operator AND a keyword |
| **Security logic detection** | Identifier keyword matching against `SEC_KW` set | Bandit-style check on function call patterns | Simple | `user`, `token`, `access` match too broadly; string literals contribute | **IMPROVE** — Remove broadest terms (`user`, `access`) or require additional signals |
| **For loop classification** | Not visited | `ast.For` as Control Logic | n/a | Missed coverage | **DEFER** — Add in 0.2.0 |
| **Try/except classification** | Not visited | `ast.Try`, `ast.ExceptHandler` | n/a | Error-handling logic missed | **DEFER** — Add in 0.2.0 |
| **Lambda classification** | Detected via `Assign` → `Lambda` body walk | Explicit `ast.Lambda` visitor | Accidentally works | Relies on `ast.walk(expr_node)` walking into Lambda.body | **KEEP** — Works; document the coverage |

---

## 3. Annotation System

| Area | Current Approach | Alternative | Current Advantages | Current Disadvantages | Recommendation |
|---|---|---|---|---|---|
| **Annotation format** | `# (L)` comment | Decorator `@logic`, docstring tag, custom AST node | No syntax change to Python | Comment-only; invisible to AST | **KEEP** — Lightweight, non-invasive, correct |
| **Preceding-line association** | `pending` flag in tokenizer loop | Line-number arithmetic (annotation_line + 1 == stmt.lineno) | Works for any whitespace | Persists across blank lines; not reset by `NEWLINE`/`NL` tokens | **IMPROVE** — Track annotation line number and check proximity: `annot_line + 1 == stmt.lineno` |
| **Inline annotation** | Same-line detection via `code_lines` set | Same | Works correctly | None | **KEEP** |
| **Multiline expression** | Line range intersection with annotation set | Same | Works correctly | None | **KEEP** |
| **String content false positive** | Tokenizer correctly treats string tokens as non-comments | regex on raw source | Correctly immune | None | **KEEP** |
| **Blank line tolerance** | Silently permissive | Strict (only immediately preceding) | More user-friendly | Inconsistent with documentation | **IMPROVE** — Either tighten implementation or update documentation to match |

---

## 4. Data Structures

| Area | Current Approach | Alternative | Current Advantages | Current Disadvantages | Recommendation |
|---|---|---|---|---|---|
| **Logic record** | `@dataclasses.dataclass` LogicRecord | NamedTuple, TypedDict, attrs, Pydantic | Built-in, mutable (for ID reassignment), type hints, `asdict()` | Fields defined on semicolon-separated lines (style concern) | **IMPROVE** — Reformat fields one-per-line for readability |
| **Category field** | `list[str]` | `frozenset[str]`, `list[Enum]` | Simple, JSON-serializable | Mutable, allows duplicates; order not guaranteed | **IMPROVE** — Use `list[str]` with deduplication; consider Enum for 0.2.0 |
| **IDs** | `LOG-NNNN` string | UUID, integer, hash | Human-readable | Mutable (reassigned after multi-file scan); not stable across runs | **KEEP** — Fine for 0.1.0; stability is a 0.2.0 concern |
| **Confidence** | `str` literals `"high"`/`"medium"`/`"low"` | Enum, float 0–1 | Simple, JSON-serializable | No validation; float scores would be misleading | **KEEP** — Qualitative levels are honest; float scores would be false precision |
| **Scan report** | `@dataclasses.dataclass` ScanReport | Plain dict | Encapsulation, methods | None | **KEEP** |

---

## 5. API Design

| Area | Current Approach | Alternative | Current Advantages | Current Disadvantages | Recommendation |
|---|---|---|---|---|---|
| **Primary API** | `scan(path)` → `ScanReport` | Multiple overloads, builder pattern | Minimal, one entry point | None | **KEEP** |
| **`scan_file()`** | Public API | Private `_scan_file()` | Allows targeted single-file scanning | Could be confused for internal use | **KEEP** — Useful for tooling integration |
| **`format_report(report)`** | Top-level function in `__all__` | Removed from `__all__` | — | Redundant: duplicates `report.format_terminal()` | **REMOVE** from `__all__` — keep internally but don't advertise |
| **JSON export** | `report.to_json()` | Separate export function | Method chaining | None | **KEEP** |
| **CLI `--strict` flag** | Exit 1 if warnings or errors | Standard linter convention | Useful for CI pipelines | None | **KEEP** |
| **CLI help exit code** | Exit 1 when no subcommand given | Exit 0 (Unix convention for `--help`) | — | Minor UX inconsistency | **IMPROVE** — Return 0 when printing help |

---

## 6. Comparable Tools

### Ruff
- **What it does**: Python linter/formatter, style and error checking
- **Overlap**: None — Ruff checks style/errors, not logic semantics
- **Lesson**: Ruff's performance comes from Rust implementation — irrelevant for NESR Logic's scope
- **Should NOT copy**: Complexity, rule system, autofixer architecture

### Pylint  
- **What it does**: General-purpose Python linter with semantic analysis
- **Overlap**: Both walk AST, both classify node types
- **What it does better**: Scope analysis (uses astroid for scope-aware AST), data-flow tracking
- **Lesson**: The `astroid` library provides enhanced AST with type inference — useful inspiration for 0.2.0
- **Should NOT copy**: The plugin system complexity, 100k+ LOC footprint

### Bandit
- **What it does**: Security-specific AST analysis (SAST)
- **Overlap**: Both detect security-relevant expressions; both use `ast` + pattern matching
- **What it does better**: Function-call tracking with import alias resolution, structured severity/confidence levels
- **Lesson**: Bandit uses `ast.NodeVisitor` subclasses mapped to node types — cleaner than `ast.walk()` dispatch
- **Should NOT copy**: External plugin infrastructure, test ID system complexity

### Flake8
- **What it does**: Python style linter with plugin architecture
- **Overlap**: Minimal — style checking only
- **Lesson**: Plugin registration pattern is extensible without reimplementing core
- **Should NOT copy**: The plugin registration system is overkill for NESR Logic 0.1.0

### Semgrep
- **What it does**: Multi-language structural pattern matching for security
- **Overlap**: Both can find security-relevant logic patterns
- **What it does better**: Pattern language, cross-file analysis, semantic matching
- **Lesson**: Semgrep uses explicit patterns users can write — this is a valid future direction for NESR Logic
- **Should NOT copy**: External rule file system, language server complexity

### NESR Logic's Genuine Independent Value
Unlike the above tools, NESR Logic uniquely:
1. **Surfaces logic as a first-class object** — not as a defect or style violation
2. **Supports developer-driven `(L)` annotation** — no other tool does this
3. **Produces structured logic records** — extractable, queryable, exportable
4. **Focuses on positive identification** — not "what's wrong" but "what's logic"

This niche is currently unoccupied.

---

## 7. Summary Decisions

| Priority | Decision | Rationale |
|---|---|---|
| 🔴 Pre-0.1.0 | **IMPROVE** expression text for `if`/`while` nodes | Currently misleading — shows whole block, not just condition |
| 🔴 Pre-0.1.0 | **IMPROVE** annotation blank-line behaviour or update docs | Spec inconsistency |
| 🟡 0.2.0 | **IMPROVE** `ast.walk()` → `ast.NodeVisitor` | Better scope tracking |
| 🟡 0.2.0 | **IMPROVE** narrow BIZ_KW/SEC_KW | Reduce false positives |
| 🟡 0.2.0 | **REMOVE** `format_report` from `__all__` | Redundant |
| 🟡 0.2.0 | **DEFER** `for`/`try` classification | Missing coverage |
| 🟢 Future | **DEFER** LibCST/symtable integration | Only if autofixing or scope analysis needed |
| 🟢 Future | **DEFER** Enum categories | Only if API stability contracts are needed |
