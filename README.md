# NESR Logic

[![PyPI version](https://img.shields.io/pypi/v/nesr-logic.svg)](https://pypi.org/project/nesr-logic/)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Dependencies](https://img.shields.io/badge/dependencies-0%20(stdlib%20only)-success.svg)](#dependencies)

**NESR Logic** is a lightweight, general-purpose Python static analysis library that discovers, extracts, classifies, and documents logical structures inside Python source code.

---

## 1. Introduction

Logic in Python codebases—such as pricing algorithms, permission checks, data validation rules, and branching policies—often becomes buried inside procedural boilerplate, helper functions, and nested expressions.

**NESR Logic** solves this by providing automated static logic discovery alongside an explicit lightweight annotation convention. It extracts structured records containing referenced inputs, output variables, inferred types, dependencies, taxonomy classifications, and actionable review warnings.

### Design Principles

- **Zero Runtime Dependencies**: Relies exclusively on Python's standard library (`ast`, `tokenize`, `dataclasses`, `json`, `pathlib`).
- **Compact & Auditable**: Core implementation is kept strictly under 200 lines of code (~175 SLOC).
- **Safe & Non-Executing**: Analyzes source code using AST and token stream without ever executing or importing the target files.
- **Independent**: Not coupled to Prolog, BIR, or BiLogic. It works as a standalone tool for any Python codebase.

---

## 2. Installation

```bash
pip install nesr-logic
```

NESR Logic requires **Python 3.10** or newer.

---

## 3. Quick Start

### Python API

```python
import nesr_logic

# Scan a single file or an entire directory tree
report = nesr_logic.scan("src/")

# Print formatted terminal report
print(report.format_terminal())

# Or export structured JSON
print(report.to_json())
```

### Command-Line Interface (CLI)

```bash
# Scan current directory
nesr-logic scan .

# Scan specific file and output JSON
nesr-logic scan app.py --json

# Strict mode (fails with exit code 1 if unannotated candidates or errors exist)
nesr-logic scan app.py --strict
```

---

## 4. Annotation Syntax

NESR Logic supports the lightweight `(L)` annotation convention to mark code regions that developers explicitly identify as critical logic.

### Supported Placement Rules

1. **Preceding Line Annotation**: Place `# (L)` on the line immediately preceding the target expression or statement:

```python
# (L)
access = user_role == "admin"
```

2. **Inline Annotation**: Place `# (L)` on the same line as the logic expression or statement:

```python
access = user_role == "admin"  # (L)
```

3. **Multiline Expressions**: The annotation applies to the entire multiline construct:

```python
# (L)
total_cost = (
    base_price
    + (tax_rate * base_price)
    - discount_amount
)
```

### Safety & Compatibility

- `(L)` is a standard Python comment. It never alters Python syntax or runtime execution.
- Comments containing literal text like `# Note: (L) model` or string literals `"Version (L)"` are disambiguated by tokenization and are **not** treated as annotations.

---

## 5. Automatic Logic Discovery

NESR Logic automatically detects unannotated logic candidates through AST pattern matching:

- **Conditional & Branching Logic**: `if` statements, ternary expressions (`x if c else y`), loop guards.
- **Boolean Logic**: Logical operators (`and`, `or`, `not`).
- **Relational Logic**: Comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `is`).
- **Arithmetic Logic**: Numeric operations (`+`, `-`, `*`, `/`, `//`, `%`, `**`).
- **Constraint Logic**: Chained inequalities (`0 <= x <= 100`), boundary bounds, assertions.
- **Validation Logic**: `isinstance`, `hasattr`, null checks (`is None`), `len` checks.
- **Business Logic**: Expressions involving pricing, tax, discounts, rates, balances, and revenue.
- **Security Logic**: Expressions involving roles, authentication, permissions, access tokens, and credentials.

When unannotated logic is detected, NESR Logic generates actionable warnings:

```text
[WARNING] Potential unannotated logic detected
File: app.py
Line: 24
Category: Security Logic / Relational Logic
Suggested action:
Review this expression and consider adding (L).
```

---

## 6. Logic Taxonomy

NESR Logic classifies detected operations into an extensible 12-category taxonomy:

| # | Category | Description / Triggers |
|---|---|---|
| 1 | **Arithmetic Logic** | Binary and unary arithmetic operators (`+`, `-`, `*`, `/`, `//`, `%`, `**`) |
| 2 | **Mathematical Logic** | Numeric calculations and math calls (`abs`, `round`, `min`, `max`, `pow`, `sqrt`, etc.) |
| 3 | **Boolean Logic** | Logical connectives (`and`, `or`, `not`) |
| 4 | **Conditional Logic** | Decision branches (`if`, `while`, ternary `if-else`) |
| 5 | **Business Logic** | Financial, transactional, and commerce rules (`price`, `tax`, `discount`, `rate`, `total`, `salary`) |
| 6 | **Decision Logic** | Branch decision gates and boolean assignments |
| 7 | **Relational Logic** | Comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `is`) |
| 8 | **Constraint Logic** | Range boundaries, chained comparisons (`a < b < c`), assertion constraints |
| 9 | **Security Logic** | Authorization, access control, identity, roles, and credential verification |
| 10 | **Validation Logic** | Type assertions, boundary guards, null checks, structure verification |
| 11 | **Control Logic** | Flow control structures, iteration conditions, and loop guards |
| 12 | **Unknown / Unclassified Logic** | Explicitly annotated operations that do not match existing syntactic heuristics |

A single operation can receive multiple applicable classifications (e.g., `role == 'admin'` is classified under **Relational Logic**, **Security Logic**, and **Decision Logic**).

---

## 7. Metadata Schema

Every logic operation discovered produces a structured `LogicRecord`:

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique operation identifier (e.g., `LOG-0001`) |
| `category` | `list[str]` | Applicable taxonomy classifications |
| `description` | `str` | Human-readable description of the operation |
| `file` | `str` | Path to source file |
| `line_start` | `int` | Starting line number (1-indexed) |
| `line_end` | `int` | Ending line number (inclusive) |
| `expression` | `str` | Exact source code snippet |
| `inputs` | `list[str]` | Variables referenced / loaded by the expression |
| `outputs` | `list[str]` | Variables assigned / produced by the statement |
| `inferred_types` | `dict[str, str]` | Statically inferable types for outputs/inputs |
| `dependencies` | `list[str]` | External functions or methods called |
| `is_annotated` | `bool` | `True` if explicitly annotated with `(L)` |
| `detection_method` | `str` | `"explicit_annotation"` or `"ast_heuristic"` |
| `confidence` | `str` | Qualitative confidence: `"high"`, `"medium"`, or `"low"` |
| `warnings` | `list[str]` | Actionable warnings and review recommendations |

---

## 8. Sample Output

### Terminal Output

```text
=== NESR Logic Scan Report: src/ ===
Total: 3 (Annotated: 1, Auto: 2, Errors: 0)

[ANNOTATED] LOG-0001 | src/auth.py:12-12 | Boolean Logic, Decision Logic, Relational Logic, Security Logic
  Expr: can_access = (role == "admin" or role == "moderator") and is_active  # (L)
  Inputs: ['is_active', 'role'] | Outputs: ['can_access'] | Types: {'can_access': 'bool'} | Conf: high

[AUTO-DETECTED] LOG-0002 | src/billing.py:45-45 | Arithmetic Logic, Mathematical Logic, Business Logic
  Expr: final_amount = base_amount * (1.0 - discount_rate)
  Inputs: ['base_amount', 'discount_rate'] | Outputs: ['final_amount'] | Types: {'final_amount': 'number'} | Conf: medium
  [WARNING] Potential unannotated logic detected
File: src/billing.py
Line: 45
Category: Arithmetic Logic / Mathematical Logic
Suggested action:
Review this expression and consider adding (L).
```

### JSON Export

```json
{
  "target": "src/",
  "summary": {
    "total_records": 2,
    "explicit_annotated": 1,
    "auto_detected": 1,
    "warnings_count": 1,
    "categories": {
      "Security Logic": 1,
      "Business Logic": 1
    },
    "errors_count": 0
  },
  "records": [
    {
      "id": "LOG-0001",
      "category": ["Security Logic", "Relational Logic"],
      "description": "Relational Logic operation",
      "file": "src/auth.py",
      "line_start": 12,
      "line_end": 12,
      "expression": "access = user_role == \"admin\"  # (L)",
      "inputs": ["user_role"],
      "outputs": ["access"],
      "inferred_types": {"access": "bool"},
      "dependencies": [],
      "is_annotated": true,
      "detection_method": "explicit_annotation",
      "confidence": "high",
      "warnings": []
    }
  ],
  "errors": []
}
```

---

## 9. Limitations & Honesty

Static analysis provides fast, safe, and automated code visibility, but it cannot achieve perfect semantic comprehension:

1. **Dynamic Values**: Values computed dynamically at runtime (e.g., via `eval`, `getattr`, or remote database fetches) cannot be statically evaluated.
2. **Duck Typing**: Python's dynamic typing means type inference without full type annotations is limited to literal and operator-inferred types.
3. **Semantic Ambiguity**: Variable names like `flag` or `data` do not carry domain context; developers should use explicit `(L)` annotations to clarify domain significance.

---

## 10. Security Considerations

- **Non-Execution**: Scanned code is never executed, evaluated, or imported.
- **Safe Parsing**: Uses Python's native `ast.parse` and `tokenize.tokenize` with graceful error recovery on malformed or broken syntax files.
- **Zero Network Activity**: No outbound connections or telemetry data are collected.

---

## 11. Contributing

Contributions are welcome! Please follow these guidelines:
1. Ensure all new features have automated tests under `tests/`.
2. Maintain the core library line count limit (< 200 nonblank, non-comment lines).
3. Ensure zero runtime external dependencies.
4. Run `pytest` to verify all tests pass.

---

## 12. License

NESR Logic is open-source software licensed under the [MIT License](LICENSE).
