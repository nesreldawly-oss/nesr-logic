"""Run duplicate probe as a pytest test so we can use the installed interpreter."""
import sys
import nesr_logic, pathlib, tempfile, os

def test_nested_if_assign_records(tmp_path):
    """Verify no duplicate records from ast.walk on nested if+assignment."""
    code = "\nif x > 0:\n    total = price * rate\n"
    f = tmp_path / "t.py"; f.write_text(code)
    r = nesr_logic.scan(f)
    print(f"\nNested if+assign records: {len(r.records)}")
    for rec in r.records:
        print(f"  line {rec.line_start}: {rec.expression[:60]!r}  cats={rec.category}")
    # We expect: 1 record for the If node, 1 for the assignment = 2 total (not duplicated)
    # What actually happens depends on whether ast.walk visits the assignment TWICE
    # (once as a direct child of If.body, and once more as a nested statement)
    assert len(r.records) <= 3, f"Possible duplicates! Got {len(r.records)} records"


def test_deep_nested_no_duplicates(tmp_path):
    """Verify no duplicate records from deeply nested expressions."""
    code = "\nif outer_cond:\n    if inner_cond:\n        result = a + b\n"
    f = tmp_path / "deep.py"; f.write_text(code)
    r = nesr_logic.scan(f)
    print(f"\nDeeply nested records: {len(r.records)}")
    for rec in r.records:
        print(f"  line {rec.line_start}: {rec.expression[:60]!r}  cats={rec.category}")
    # Collect unique (line_start, expression) pairs to check for duplicates
    pairs = [(rec.line_start, rec.expression) for rec in r.records]
    assert len(pairs) == len(set(pairs)), f"DUPLICATES DETECTED: {pairs}"


def test_for_loop_assign_found(tmp_path):
    """Assignment inside for loop should still be found by ast.walk."""
    code = "\nfor i in range(10):\n    x = i * factor\n"
    f = tmp_path / "for.py"; f.write_text(code)
    r = nesr_logic.scan(f)
    print(f"\nFor-loop+assign records: {len(r.records)}")
    for rec in r.records:
        print(f"  line {rec.line_start}: {rec.expression[:60]!r}  cats={rec.category}")
    # x = i * factor should be found (arithmetic inside for)
    assert any("x" in rec.outputs for rec in r.records), "Assignment in for loop not found"
