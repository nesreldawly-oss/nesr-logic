"""Tests for logic taxonomy categories and expression structures."""
import pathlib
import pytest
import nesr_logic


def test_boolean_logic(tmp_path: pathlib.Path):
    """Test 4: Boolean logic discovery (and, or, not)."""
    code = '''
is_eligible = (has_account and is_verified) or not is_suspended
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert "Boolean Logic" in rec.category
    assert "Decision Logic" in rec.category
    assert set(rec.inputs) == {"has_account", "is_suspended", "is_verified"}
    assert rec.outputs == ["is_eligible"]
    assert rec.inferred_types.get("is_eligible") == "bool"


def test_arithmetic_expressions(tmp_path: pathlib.Path):
    """Test 5: Arithmetic expressions discovery (+, -, *, /)."""
    code = '''
net_salary = gross_salary - income_tax - social_security
monthly_rate = annual_rate / 12
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 2
    r1, r2 = report.records
    assert "Arithmetic Logic" in r1.category
    assert "Mathematical Logic" in r1.category
    assert "net_salary" in r1.outputs

    assert "Arithmetic Logic" in r2.category
    assert r2.inferred_types.get("monthly_rate") == "float"


def test_conditional_structures(tmp_path: pathlib.Path):
    """Test 6: Conditional structures discovery (if, ternary)."""
    code = '''
if threshold > 100:
    pass

status = "active" if count > 0 else "inactive"
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 2
    r1, r2 = report.records
    assert "Conditional Logic" in r1.category
    assert "Control Logic" in r1.category
    assert "Relational Logic" in r1.category

    assert "Conditional Logic" in r2.category
    assert "Decision Logic" in r2.category
    assert r2.outputs == ["status"]


def test_business_rule_candidates(tmp_path: pathlib.Path):
    """Test 7: Business-rule candidates detection."""
    code = '''
discount_amount = price * discount_rate
total_invoice = (subtotal + tax_amount) - discount_amount
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 2
    for r in report.records:
        assert "Business Logic" in r.category
        assert "Arithmetic Logic" in r.category


def test_security_related_candidates(tmp_path: pathlib.Path):
    """Test 8: Security-related candidates detection."""
    code = '''
can_edit = (user_role == "admin") or (user_token is not None and is_authenticated)
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert "Security Logic" in rec.category
    assert "Boolean Logic" in rec.category
    assert "Relational Logic" in rec.category


def test_multiple_classifications(tmp_path: pathlib.Path):
    """Test 9: Multiple classifications applied simultaneously."""
    code = '''
is_admin_allowed = (user_role == "admin") and (access_limit > 50)
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    # Should match: Relational, Boolean, Security, Constraint, Decision
    assert "Relational Logic" in rec.category
    assert "Boolean Logic" in rec.category
    assert "Security Logic" in rec.category
    assert "Constraint Logic" in rec.category
    assert "Decision Logic" in rec.category


def test_nested_expressions(tmp_path: pathlib.Path):
    """Test 10: Nested expressions discovery."""
    code = '''
result = ((base + adjustment) * factor) > ((threshold - safety_margin) / divisor)
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert "Relational Logic" in rec.category
    assert "Arithmetic Logic" in rec.category
    assert "Mathematical Logic" in rec.category
    expected_inputs = {"adjustment", "base", "divisor", "factor", "safety_margin", "threshold"}
    assert set(rec.inputs) == expected_inputs
    assert rec.outputs == ["result"]


def test_all_twelve_categories(tmp_path: pathlib.Path):
    """Verify each of the 12 taxonomy categories can be detected."""
    code = '''
# 1 & 2: Arithmetic & Mathematical
val1 = x + y
# 3: Boolean
val2 = a and b
# 4 & 11: Conditional & Control
if flag:
    pass
# 5: Business
val3 = price * 0.1
# 6: Decision
valid = count > 0
# 7: Relational
val4 = x == y
# 8: Constraint
valid_range = 0 < x < 100
# 9: Security
is_auth = user_token is not None
# 10: Validation
is_valid_type = isinstance(data, list)
# 12: Unknown / Unclassified Logic
# (L)
custom_action(foo, bar)
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    all_cats = set()
    for r in report.records:
        all_cats.update(r.category)

    expected = {
        "Arithmetic Logic",
        "Mathematical Logic",
        "Boolean Logic",
        "Conditional Logic",
        "Business Logic",
        "Decision Logic",
        "Relational Logic",
        "Constraint Logic",
        "Security Logic",
        "Validation Logic",
        "Control Logic",
        "Unknown / Unclassified Logic",
    }
    for cat in expected:
        assert cat in all_cats, f"Expected taxonomy category {cat} was not found in: {all_cats}"
