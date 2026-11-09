"""Tests for explicit and inline (L) annotation detection."""
import tempfile
import pathlib
import pytest
import nesr_logic


def test_explicit_preceding_annotation(tmp_path: pathlib.Path):
    """Test 1: Explicit (L) annotation preceding the target logic statement."""
    code = '''
# (L)
access_granted = user_role == "admin"
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert rec.is_annotated is True
    assert rec.detection_method == "explicit_annotation"
    assert rec.confidence == "high"
    assert "access_granted" in rec.outputs
    assert "user_role" in rec.inputs
    assert "Security Logic" in rec.category
    assert "Relational Logic" in rec.category
    assert len(rec.warnings) == 0


def test_inline_annotation(tmp_path: pathlib.Path):
    """Test 2: Inline (L) annotation on the same line."""
    code = '''
access = user_role == "admin"  # (L)
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert rec.is_annotated is True
    assert rec.detection_method == "explicit_annotation"
    assert rec.confidence == "high"
    assert rec.outputs == ["access"]


def test_missing_annotation_detection(tmp_path: pathlib.Path):
    """Test 3: Missing annotation detection produces actionable warnings."""
    code = '''
access = user_role == "admin"
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert rec.is_annotated is False
    assert rec.detection_method == "ast_heuristic"
    assert len(rec.warnings) == 1
    assert "[WARNING] Potential unannotated logic detected" in rec.warnings[0]
    assert "Suggested action:" in rec.warnings[0]
    assert "Review this expression and consider adding (L)." in rec.warnings[0]


def test_multiline_annotated_expression(tmp_path: pathlib.Path):
    """Test 11: Multiline expressions with annotation."""
    code = '''
# (L)
total_cost = (
    base_price
    + (tax_rate * base_price)
    - discount_amount
)
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    assert len(report.records) == 1
    rec = report.records[0]
    assert rec.is_annotated is True
    assert rec.line_start == 3
    assert rec.line_end == 7
    assert "total_cost" in rec.outputs
    assert "base_price" in rec.inputs
    assert "discount_amount" in rec.inputs
    assert "tax_rate" in rec.inputs
    assert "Business Logic" in rec.category
    assert "Arithmetic Logic" in rec.category


def test_comments_and_strings_literal_l(tmp_path: pathlib.Path):
    """Test 12: Comments and strings containing literal '(L)' are NOT treated as annotations."""
    code = '''
# This is a model (L) configuration note that should not trigger annotation
description = "System model (L) series 3000"
price = 100 * quantity
'''
    f = tmp_path / "app.py"
    f.write_text(code, encoding="utf-8")
    report = nesr_logic.scan(f)

    # description = "..." is not logic and literal "(L)" inside string is not an annotation
    # price = 100 * quantity is auto-detected arithmetic logic, but NOT annotated!
    annotated = [r for r in report.records if r.is_annotated]
    assert len(annotated) == 0, f"Expected 0 annotated records, found: {annotated}"

    auto = [r for r in report.records if not r.is_annotated]
    assert len(auto) == 1
    assert auto[0].outputs == ["price"]
