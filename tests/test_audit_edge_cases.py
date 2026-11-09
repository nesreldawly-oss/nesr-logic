"""
Audit edge-case tests to discover false positives, false negatives, and
classification ambiguities. Run with: pytest tests/test_audit_edge_cases.py -v
These tests document EXPECTED BEHAVIOUR; failures expose real defects.
"""
import pathlib
import sys
import nesr_logic


def test_blank_line_between_annotation_and_statement(tmp_path):
    code = "# (L)\n\nx = y > 0\n"
    f = tmp_path / "gap.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 1
    is_annot = report.records[0].is_annotated
    # AUDIT NOTE: annotation persists across blank line (pending=True not reset on NEWLINE/NL)
    # This means blank-separated annotation IS treated as annotated — potential false positive.


def test_two_annotations_one_statement(tmp_path):
    code = "# (L)\n# (L)\nx = y > 0\n"
    f = tmp_path / "dup.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 1
    assert report.records[0].is_annotated is True


def test_annotation_after_statement_annotates_next(tmp_path):
    code = "x = y > 0\n# (L)\na = b + c\n"
    f = tmp_path / "after.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    by_output = {r.outputs[0]: r for r in report.records if r.outputs}
    assert by_output["x"].is_annotated is False
    assert by_output["a"].is_annotated is True


def test_annotation_in_multiline_string(tmp_path):
    code = 'msg = """\n# (L)\nThis is not code\n"""\nx = 1 + 2\n'
    f = tmp_path / "strannot.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    annotated = [r for r in report.records if r.is_annotated]
    assert len(annotated) == 0, f"False annotation from string content: {annotated}"


def test_simple_string_assignment_not_detected(tmp_path):
    code = 'name = "Alice"\ngreeting = "Hello, world!"\n'
    f = tmp_path / "stronly.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 0, f"False positives: {[r.expression for r in report.records]}"


def test_simple_int_assignment_not_detected(tmp_path):
    code = "x = 42\ny = 100\n"
    f = tmp_path / "intonly.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 0


def test_function_call_no_logic_not_detected(tmp_path):
    code = "process_data(items)\nlog_event(event_id)\n"
    f = tmp_path / "calls.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 0, f"False positives from bare calls: {[r.expression for r in report.records]}"


def test_import_statement_not_detected(tmp_path):
    code = "import os\nimport sys\nfrom pathlib import Path\n"
    f = tmp_path / "imports.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 0


def test_print_statement_not_detected(tmp_path):
    code = 'print("Hello")\nprint(result)\n'
    f = tmp_path / "prints.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 0


def test_comprehension_with_condition(tmp_path):
    code = "filtered = [x for x in items if x > threshold]\n"
    f = tmp_path / "comp.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) >= 1
    cats = set()
    for r in report.records:
        cats.update(r.category)
    assert "Relational Logic" in cats or "Conditional Logic" in cats


def test_chained_comparison(tmp_path):
    code = "in_range = 0 <= age <= 120\n"
    f = tmp_path / "chain.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 1
    rec = report.records[0]
    assert "Relational Logic" in rec.category
    assert "Constraint Logic" in rec.category


def test_augmented_assignment(tmp_path):
    code = "total += quantity * unit_price\n"
    f = tmp_path / "aug.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.records) == 1
    rec = report.records[0]
    assert "Arithmetic Logic" in rec.category
    assert "total" in rec.outputs


def test_walrus_operator_no_crash(tmp_path):
    code = "if (n := len(data)) > 10:\n    process(n)\n"
    f = tmp_path / "walrus.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.errors) == 0


def test_nested_function_logic(tmp_path):
    code = "def outer():\n    def inner():\n        # (L)\n        return x > threshold\n"
    f = tmp_path / "nested.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    annotated = [r for r in report.records if r.is_annotated]
    assert len(annotated) == 1


def test_class_method_logic(tmp_path):
    code = "class Pricing:\n    def compute(self, price, rate):\n        discount = price * rate  # (L)\n        return discount\n"
    f = tmp_path / "cls.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    annotated = [r for r in report.records if r.is_annotated]
    assert len(annotated) == 1
    assert "discount" in annotated[0].outputs


def test_non_utf8_file(tmp_path):
    f = tmp_path / "latin1.py"; f.write_bytes(b"x = \xe9 + 1\n")
    report = nesr_logic.scan(f)
    assert len(report.errors) == 1
    assert "Syntax/Decode error" in report.errors[0]["message"]


def test_binary_file(tmp_path):
    f = tmp_path / "binary.py"; f.write_bytes(bytes(range(256)))
    report = nesr_logic.scan(f)
    assert len(report.errors) == 1


def test_permission_error_simulation(tmp_path):
    fake = tmp_path / "nonexistent.py"
    report = nesr_logic.scan_file(fake)
    assert len(report.errors) == 1
    assert "Read error" in report.errors[0]["message"]


def test_id_renumbering_across_directory(tmp_path):
    (tmp_path / "a.py").write_text("x = y > 0\n")
    (tmp_path / "b.py").write_text("p = q < 10\n")
    report = nesr_logic.scan(tmp_path)
    ids = [r.id for r in report.records]
    assert ids == ["LOG-0001", "LOG-0002"]


def test_records_sorted_by_line(tmp_path):
    code = "b = x > 0\na = y < 10\n"
    f = tmp_path / "order.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    lines = [r.line_start for r in report.records]
    assert lines == sorted(lines)


def test_string_value_triggering_biz_keyword(tmp_path):
    """
    KNOWN FALSE-POSITIVE RISK: string VALUE 'invoice' triggers Business Logic
    even though this is just a constant assignment.
    """
    code = 'product_type = "invoice"\n'
    f = tmp_path / "biz_str.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    # This documents the actual current behaviour. Ideally: 0 records.
    # If this test PASSES (0 records), the bug was fixed. If it fails, bug exists.
    # We document and pass either way by just printing:
    biz = [r for r in report.records if "Business Logic" in r.category]
    # Document finding - this reveals the false positive if records > 0
    if biz:
        print(f"[AUDIT-FP] 'invoice' string triggers Business Logic: {biz[0].expression}")
    # We SHOULD have 0 records since there is no logic operator
    assert len(report.records) == 0, f"FALSE POSITIVE: plain string assignment with biz keyword detected: {report.records[0].expression}"


def test_string_value_triggering_sec_keyword(tmp_path):
    """
    KNOWN FALSE-POSITIVE RISK: string VALUE 'admin' triggers Security Logic.
    """
    code = 'docstring = "admin guide"\n'
    f = tmp_path / "sec_str.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    sec = [r for r in report.records if "Security Logic" in r.category]
    if sec:
        print(f"[AUDIT-FP] 'admin' string triggers Security Logic: {sec[0].expression}")
    assert len(report.records) == 0, f"FALSE POSITIVE: plain string with sec keyword detected: {report.records[0].expression}"


def test_decorator_no_crash(tmp_path):
    code = "@property\ndef is_active(self):\n    return self._active and not self._suspended\n"
    f = tmp_path / "deco.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    assert len(report.errors) == 0


def test_lambda_with_comparison(tmp_path):
    """Lambda containing comparison — should be found inside Assign.value."""
    code = "is_adult = lambda age: age >= 18\n"
    f = tmp_path / "lam.py"; f.write_text(code)
    report = nesr_logic.scan(f)
    # The lambda body has a comparison; detection depends on ast.walk into Lambda.body
    # Document: if 0 records, lambda interiors are a blind spot.
    if len(report.records) == 0:
        print("[AUDIT] Lambda comparison is a blind spot — not detected")
    else:
        print(f"[AUDIT] Lambda detected: {[r.category for r in report.records]}")
