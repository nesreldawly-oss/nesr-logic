# Changelog

All notable changes to **NESR Logic** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-09

### Added
- Initial release of **NESR Logic** (`nesr-logic`).
- Standalone, general-purpose Python static analysis library for logic discovery and extraction.
- Zero external runtime dependencies (Python standard library only).
- Compact core implementation (< 200 nonblank, non-comment lines of code).
- Explicit `(L)` annotation support via Python Tokenizer (both preceding line `# (L)` and inline `# (L)`).
- Automatic logic discovery for conditionals, comparisons, boolean operations, arithmetic expressions, validation conditions, and decision trees.
- Initial 12-category taxonomy:
  1. Arithmetic Logic
  2. Mathematical Logic
  3. Boolean Logic
  4. Conditional Logic
  5. Business Logic
  6. Decision Logic
  7. Relational Logic
  8. Constraint Logic
  9. Security Logic
  10. Validation Logic
  11. Control Logic
  12. Unknown / Unclassified Logic
- Structured metadata extraction: Logic ID, categories, description, source location, expression, inputs, outputs, inferred types, dependencies, annotation status, detection method, confidence level, and actionable warnings.
- Public Python API: `nesr_logic.scan()`, `nesr_logic.scan_file()`, `nesr_logic.format_report()`.
- Command-line interface: `nesr-logic scan <path> [--json] [--strict]`.
- Human-readable terminal report and full JSON export.
- Safe static analysis: never executes analyzed source code.
