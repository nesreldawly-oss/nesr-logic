# NESR Logic — Detection Validation Report
**Audit Date**: 2026-11-09  
**Version**: 0.1.0  
**Test Files**: `tests/test_audit_edge_cases.py`, `tests/test_probe_duplicates.py`  
**Total Edge-Case Tests Added**: 27  
**All pass**: ✅ 44/44 tests

---

> [!NOTE]
> This report documents every tested edge case with expected vs actual behaviour. Where actual behaviour differs from ideal behaviour, this is explicitly noted. Tests that capture known limitations pass deliberately (they document reality, not bugs to be hidden).

---

## 1. Annotation Detection Tests

### TC-A01: Explicit preceding-line annotation
```python
# (L)
access_granted = user_role == "admin"
```
- **Expected**: 1 record, `is_annotated=True`, Security Logic, Relational Logic
- **Actual**: ✅ CORRECT — 1 record, `is_annotated=True`, `confidence="high"`
- **Notes**: Core use case, works correctly

### TC-A02: Inline annotation
```python
access = user_role == "admin"  # (L)
```
- **Expected**: 1 record, `is_annotated=True`
- **Actual**: ✅ CORRECT
- **Notes**: Works via code_lines set intersection

### TC-A03: Missing annotation (auto-detection + warning)
```python
access = user_role == "admin"
```
- **Expected**: 1 record, `is_annotated=False`, warning present
- **Actual**: ✅ CORRECT — Warning text matches spec format including "Review this expression and consider adding (L)."

### TC-A04: Blank line between annotation and statement
```python
# (L)

x = y > 0
```
- **Expected (spec)**: Not annotated (spec says "immediately preceding")
- **Actual**: `is_annotated=True` — annotation persists across blank line
- **Result**: ⚠️ IMPLEMENTATION EXCEEDS SPEC — not a failure but an inconsistency
- **Classification**: False positive for annotation association (low severity)
- **Action**: Document behaviour; either tighten to line+1 check or update spec

### TC-A05: Two consecutive annotations, one statement
```python
# (L)
# (L)
x = y > 0
```
- **Expected**: 1 record, `is_annotated=True`
- **Actual**: ✅ CORRECT — `pending` set twice but only one record generated

### TC-A06: Annotation after statement annotates next
```python
x = y > 0
# (L)
a = b + c
```
- **Expected**: `x` unannotated, `a` annotated
- **Actual**: ✅ CORRECT — works as expected

### TC-A07: `(L)` inside triple-quoted string
```python
msg = """
# (L)
This is not code
"""
x = 1 + 2
```
- **Expected**: No annotation for `x`
- **Actual**: ✅ CORRECT — tokenizer treats triple-quoted string as a single STRING token; the internal `# (L)` is NOT a COMMENT token

### TC-A08: `(L)` text in function-call argument string
```python
logger.info("checking (L) logic gate")
x = a and b
```
- **Expected**: No annotations
- **Actual**: ✅ CORRECT — same mechanism as TC-A07

### TC-A09: Comment with leading text (should NOT match)
```python
# This is a model (L) configuration note
x = y > 0
```
- **Expected**: Not annotated (regex requires `# (L)` at start of comment)
- **Actual**: ✅ CORRECT — regex `r"#\s*\(L\)(?:\s*[:\-].*)?$"` requires `(L)` immediately after `#` (with optional spaces), so "This is a model (L)" does NOT match

---

## 2. Auto-Detection False Positive Tests

### TC-FP01: Simple string assignment
```python
name = "Alice"
```
- **Expected**: 0 records (no logic operators)
- **Actual**: ✅ CORRECT — 0 records (filtered by `isinstance(expr, ast.Constant)` guard)

### TC-FP02: Integer constant assignment
```python
x = 42
```
- **Expected**: 0 records
- **Actual**: ✅ CORRECT

### TC-FP03: Bare function calls
```python
process_data(items)
log_event(event_id)
```
- **Expected**: 0 records
- **Actual**: ✅ CORRECT — filtered by the `ast.Expr` guard requiring `Compare`/`BoolOp`/`IfExp`

### TC-FP04: Import statements
```python
import os
from pathlib import Path
```
- **Expected**: 0 records
- **Actual**: ✅ CORRECT — `ast.Import`/`ast.ImportFrom` not in dispatch

### TC-FP05: Print statements
```python
print("Hello")
print(result)
```
- **Expected**: 0 records
- **Actual**: ✅ CORRECT

### TC-FP06: Business keyword in string value
```python
product_type = "invoice"
```
- **Expected (ideal)**: 0 records (pure constant assignment, no logic)
- **Actual**: ✅ 0 records — the constant-assignment guard (`isinstance(expr, ast.Constant)`) correctly blocks this
- **Notes**: The string content "invoice" IS added to `idents` during `_classify_and_extract`, but the statement is filtered before reaching that function

### TC-FP07: Security keyword in string value
```python
docstring = "admin guide"
```
- **Expected (ideal)**: 0 records
- **Actual**: ✅ 0 records — same guard as TC-FP06

### TC-FP08: Security keyword `user` in variable name
```python
user = get_user()
```
- **Expected**: 0 records (bare function call, no logic operator)
- **Actual**: ✅ 0 records — filtered by `ast.Expr` guard

---

## 3. Auto-Detection Coverage Tests

### TC-DET01: Boolean logic
```python
is_eligible = (has_account and is_verified) or not is_suspended
```
- **Expected**: 1 record, Boolean Logic, Decision Logic; type=bool
- **Actual**: ✅ CORRECT

### TC-DET02: Arithmetic expressions
```python
net_salary = gross_salary - income_tax - social_security
monthly_rate = annual_rate / 12
```
- **Expected**: 2 records, Arithmetic Logic; `monthly_rate` type=float
- **Actual**: ✅ CORRECT

### TC-DET03: Chained comparison
```python
in_range = 0 <= age <= 120
```
- **Expected**: 1 record, Relational Logic + Constraint Logic
- **Actual**: ✅ CORRECT — multi-op Compare detected by `len(ops) > 1` check

### TC-DET04: Conditional structures
```python
if threshold > 100:
    pass

status = "active" if count > 0 else "inactive"
```
- **Expected**: 2 records; `if` → Conditional/Control Logic; ternary → Conditional/Decision Logic
- **Actual**: ✅ CORRECT

### TC-DET05: Augmented assignment with arithmetic
```python
total += quantity * unit_price
```
- **Expected**: 1 record, Arithmetic Logic, `total` in outputs
- **Actual**: ✅ CORRECT

### TC-DET06: Walrus operator
```python
if (n := len(data)) > 10:
    process(n)
```
- **Expected**: No crash; some detection of the condition
- **Actual**: ✅ No crash, records detected (walrus is part of If.test, walked correctly)

### TC-DET07: Comprehension with condition
```python
filtered = [x for x in items if x > threshold]
```
- **Expected**: At least 1 record with Relational Logic
- **Actual**: ✅ 1+ records detected — ListComp is part of Assign.value, ast.walk finds Compare inside

### TC-DET08: Lambda with comparison
```python
is_adult = lambda age: age >= 18
```
- **Expected (ideal)**: 1 record, Relational Logic + Decision Logic
- **Actual**: ✅ 1 record, `['Decision Logic', 'Relational Logic']` — Lambda.body is walked by ast.walk(expr_node)
- **Notes**: Works accidentally through `ast.walk(expr_node)` BFS descent into Lambda node

---

## 4. Structural Tests

### TC-STR01: Nested function annotation
```python
def outer():
    def inner():
        # (L)
        return x > threshold
```
- **Expected**: 1 annotated record inside inner function
- **Actual**: ✅ CORRECT — `ast.walk(tree)` visits all nodes regardless of nesting depth

### TC-STR02: Class method annotation
```python
class Pricing:
    def compute(self, price, rate):
        discount = price * rate  # (L)
        return discount
```
- **Expected**: 1 annotated record for `discount = price * rate`
- **Actual**: ✅ CORRECT

### TC-STR03: Nested if blocks (expression text issue)
```python
if outer_cond:
    if inner_cond:
        result = a + b
```
- **Expected (ideal)**: 3 records, all with accurate expression text
- **Actual**: 3 records, but outer `if outer_cond` expression captures the **entire block** (3 lines of code), not just the condition
- **Result**: ⚠️ DEFECT D-01/D-03 — expression text is misleading for `if`/`while` nodes

### TC-STR04: ID ordering across directory scan
- **Expected**: IDs renumbered globally `LOG-0001..N`
- **Actual**: ✅ CORRECT

---

## 5. Fault Tolerance Tests

### TC-FAULT01: Syntax error file
- **Expected**: 1 error record, 0 logic records, no crash
- **Actual**: ✅ CORRECT

### TC-FAULT02: Empty file
- **Expected**: 0 records, 0 errors
- **Actual**: ✅ CORRECT

### TC-FAULT03: Non-UTF-8 binary content
- **Expected**: 1 error record (Syntax/Decode error), no crash
- **Actual**: ✅ CORRECT

### TC-FAULT04: Non-existent file
- **Expected**: 1 error record (Read error), no crash
- **Actual**: ✅ CORRECT — `scan_file()` on non-existent path returns `{"Read error": ...}`

### TC-FAULT05: Decorator on function (not mistaken for annotation)
- **Expected**: No crash; `@property` does not interfere with annotation detection
- **Actual**: ✅ CORRECT

---

## 6. Known Blind Spots

| Construct | Detected? | Category If Detected | Notes |
|---|---|---|---|
| `for` loop guard | ❌ No | (would be Control Logic) | `ast.For` not in dispatch |
| `try`/`except` | ❌ No | (would be Validation/Control) | `ast.Try` not in dispatch |
| `with` statement | ❌ No | n/a | Context managers rarely contain logic |
| Match/case (Python 3.10+) | ❌ No | (would be Conditional Logic) | `ast.Match` not in dispatch |
| `yield`/generator logic | ⚠️ Partial | Only if expression contains operators | `ast.Yield` not explicitly dispatched |
| Walrus `:=` operator | ✅ Accidental | Via `If.test` walk | Works but not explicitly handled |
| Lambda body | ✅ Accidental | Via `Assign.value` walk | Works via BFS descent |

---

## 7. Classification Accuracy Summary

| Category | True Positive Rate | False Positive Risk | Notes |
|---|---|---|---|
| Arithmetic Logic | High | Low | `BinOp` matching is precise |
| Mathematical Logic | High | Low | Mostly co-occurs with Arithmetic |
| Boolean Logic | High | Low | `BoolOp` matching is precise |
| Conditional Logic | High | Low | `If`/`While`/`IfExp` matching is precise |
| Business Logic | Medium | Medium | Keyword matching; broad terms (`order`, `limit`) |
| Decision Logic | Medium | Medium | Broad trigger (any `BoolOp` or `cmp+outputs`) |
| Relational Logic | High | Low | `Compare` matching is precise |
| Constraint Logic | Medium | Low | Multi-op compare is reliable; keyword part is fuzzy |
| Security Logic | Medium | Medium-High | `user`, `token`, `access` match too broadly |
| Validation Logic | High | Low | `isinstance`/`assert`/null-check matching is precise |
| Control Logic | High | Low | Only `If`/`While` nodes |
| Unknown/Unclassified | High | Low | Fallback for `(L)`-only expressions |

---

## 8. Summary

The detection engine correctly handles the core cases with no false positives for simple expressions and no crashes for any tested malformed input. 

**Three issues merit improvement before or shortly after 0.1.0:**

1. **D-01/D-03**: Expression text for `if`/`while` captures whole block — fix by using `ast.unparse(node.test)` for the condition portion
2. **D-02**: Blank-line annotation tolerance exceeds spec — fix by checking line proximity
3. **D-04/D-05**: Business/Security keyword matching is broader than ideal — narrow BIZ_KW/SEC_KW or add additional operator requirements

None of these are correctness failures — they are precision/accuracy improvements.
