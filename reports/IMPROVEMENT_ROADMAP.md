# NESR Logic — Improvement Roadmap

**Document Version**: 1.0  
**Audit Reference**: 2026-11-09 Technical Audit & Comparative Research  
**Target Milestone**: 0.1.0 Release Candidate & Beyond  

---

## 1. Overview and Prioritization Framework

This roadmap defines the engineering priorities for NESR Logic across three distinct horizons:

1. **Phase 1: Required Before 0.1.0 (Critical Polish & Correctness)**  
   Targeted fixes that directly impact user-facing output precision, specification consistency, or CLI conventions without altering core architecture or breaching the <= 200 SLOC budget.
2. **Phase 2: Recommended for 0.2.0 (Structural & Classification Enhancements)**  
   Evolution of internal AST traversal, vocabulary refinement, expanded syntactic coverage (e.g., `for`, `try/except`, `match/case`), and cleaner record presentation.
3. **Phase 3: Long-Term Research & Ecosystem Extensions (0.3.0+)**  
   Language Server Protocol (LSP) diagnostics, IDE plugins, graph visualizations, type-stub integration, and custom user-defined logic rule packs.

---

## 2. Phase 1: Required Before Version 0.1.0

These changes address confirmed defects identified in `reports/TECHNICAL_AUDIT.md` and `reports/DETECTION_VALIDATION.md`. They require user approval before implementation.

### Item 1.1: Truncate / Isolate Expression Text for Block Statements (Defect D-01 / D-03)
- **Problem**: For `if`, `while`, and `assert` statements, `node.lineno` through `node.end_lineno` extracts the entire block (including nested inner code). For example, an `if` block with 10 lines prints all 10 lines as the `expression`, rather than the condition expression being evaluated.
- **Proposed Solution**: 
  - For `ast.If` and `ast.While`, record `expr_text` from `stmt.test` (or `ast.unparse(stmt.test)` where available, or slice lines using `stmt.test.lineno` to `stmt.test.end_lineno`).
  - Keep `line_start` and `line_end` scoped to the actual logic test or statement header.
- **Impact on SLOC**: ~3 lines change in `src/nesr_logic/__init__.py`.
- **Breaking Change**: No. Enhances output quality.

### Item 1.2: Enforce Strict Line Proximity for Preceding-Line `# (L)` Annotations (Defect D-02)
- **Problem**: The tokenizer's `pending` flag currently persists across blank lines. If `# (L)` is followed by two blank lines and then code, the statement is still treated as explicitly annotated, which contradicts the documented rule ("on the line immediately preceding").
- **Proposed Solution**: 
  - Track the exact line number where `# (L)` occurred (`annot_comment_line`).
  - When the next code token arrives on `tok_line`, only associate the annotation if `tok_line == annot_comment_line + 1` (or document the multiline blank-line tolerance explicitly).
  - Clear `pending` when a newline or non-adjacent token arrives.
- **Impact on SLOC**: ~2 lines change.
- **Breaking Change**: No. Aligns implementation with specification.

### Item 1.3: CLI Exit Code Normalization on `--help` / Empty Invocation
- **Problem**: Calling `nesr-logic` without arguments currently prints help and returns exit code `1`. Standard Unix and Python CLI tooling (e.g. `pytest`, `ruff`) returns exit code `0` on `--help` and standard usage help.
- **Proposed Solution**: Ensure `parser.parse_args()` default invocation with no arguments exits cleanly with code `0` when help is requested, or provides a concise usage line.
- **Impact on SLOC**: 1 line change.

### Item 1.4: Refactor Semicolon-Separated Dataclass Fields
- **Problem**: `LogicRecord` currently clusters fields on single lines separated by semicolons (`id: str; category: list[str]; ...`) to satisfy line limits. While syntactically valid Python, it impairs code readability and PEP 8 style.
- **Proposed Solution**: Group fields cleanly or use standard multiline field definitions while keeping the core library comfortably within the 180–190 SLOC envelope.

---

## 3. Phase 2: Recommended for Version 0.2.0

### Item 2.1: Migrate Traversal from `ast.walk()` to `ast.NodeVisitor`
- **Problem**: `ast.walk()` is a flat BFS queue that discards scope context. It prevents knowing whether an expression is inside a function, class method, comprehension, or top-level script.
- **Proposed Solution**: Implement a lightweight subclass of `ast.NodeVisitor` (or stack-based descent). Track scope (`current_function`, `current_class`) and attach scope metadata to `LogicRecord`.
- **Target Release**: 0.2.0.

### Item 2.2: Refine Semantic Keyword Matching to Reduce False Positives
- **Problem**: Generic keywords such as `"user"`, `"order"`, and `"limit"` generate false positives for Security Logic and Business Logic when they appear in mundane variables (e.g. `order_by_name`, `user_avatar_color`).
- **Proposed Solution**:
  - Restrict `SEC_KW` by removing overly broad substrings (`user` -> `user_role`, `user_perm`, `auth_user`).
  - Require a compound trigger: an identifier must match `SEC_KW` **and** be involved in a comparison or boolean check to be classified as Security Logic.
- **Target Release**: 0.2.0.

### Item 2.3: Expand Control & Validation Coverage (`for`, `try/except`, `match/case`)
- **Problem**: Python 3.10 `match/case` statements and traditional `for/while` loops represent fundamental control logic, but `match` and `for` are omitted from the current dispatch.
- **Proposed Solution**:
  - Add `ast.For` and `ast.AsyncFor` to Control Logic.
  - Add `ast.Match` (Python 3.10+) to Conditional / Decision Logic.
  - Add `ast.Try` and `ast.ExceptHandler` to Validation / Control Logic.
- **Target Release**: 0.2.0.

### Item 2.4: Deprecate Redundant Top-Level `format_report`
- **Problem**: `nesr_logic.format_report(report)` duplicates `report.format_terminal()`.
- **Proposed Solution**: Remove `format_report` from `__all__` and guide users toward `report.format_terminal()` and `str(report)`.
- **Target Release**: 0.2.0.

---

## 4. Phase 3: Long-Term Research & Ecosystem Extensions (0.3.0+)

### Item 3.1: Language Server Protocol (LSP) Diagnostics
- Enable real-time in-editor highlighting of unannotated logic candidates.
- Provide a quick-fix code action: *"Add # (L) annotation"*.
- Architecture: Standalone lightweight CLI daemon (`nesr-logic lsp`) using standard stdlib JSON-RPC over stdin/stdout.

### Item 3.2: Export to Logic Graph Formats (Mermaid / Graphviz)
- Transform extracted conditional and decision records into directed decision graphs:
  - Mermaid: `graph TD; A[user_role == 'admin'] -->|True| B[access = True]`
  - Graphviz DOT format for automated architecture diagram generation.

### Item 3.3: User-Configurable Custom Taxonomies & Rule Packs
- Allow organizations to supply a `.nesr-logic.toml` configuration file specifying custom keywords, domain rules, and company-specific classification tags (e.g., `HIPAA Compliance Logic`, `Billing Gateways`).

---

## 5. Summary of Recommended Action Plan

```
[Now: Present Audit & Roadmap]
           │
           ▼
[Awaiting User Approval on Phase 1 Items]
           │
 ┌─────────┴─────────┐
 ▼                   ▼
[Approval Given]   [Modifications Requested]
 │                   │
 ▼                   ▼
[Implement Phase 1] [Adjust Priorities]
 │
 ▼
[Verify Tests & SLOC < 200]
 │
 ▼
[Publish Release Candidate v0.1.0]
```
