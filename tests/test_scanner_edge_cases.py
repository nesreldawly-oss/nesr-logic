"""Edge cases, safety, serialization, and CLI testing."""
import json
import pathlib
import sys
import pytest
import nesr_logic


def test_syntax_errors(tmp_path: pathlib.Path):
    """Test 13: Syntax errors are handled gracefully without crashing."""
    f = tmp_path / "broken.py"
    f.write_text("def broken_syntax(:\n    return ===\n", encoding="utf-8")

    report = nesr_logic.scan(f)
    assert len(report.errors) == 1
    assert "Syntax/Decode error" in report.errors[0]["message"]
    assert len(report.records) == 0


def test_empty_files(tmp_path: pathlib.Path):
    """Test 14: Empty files return empty records and no errors."""
    f = tmp_path / "empty.py"
    f.write_text("", encoding="utf-8")

    report = nesr_logic.scan(f)
    assert len(report.records) == 0
    assert len(report.errors) == 0


def test_multiple_python_files(tmp_path: pathlib.Path):
    """Test 15: Multiple Python files scanned across directories."""
    sub1 = tmp_path / "sub1"
    sub2 = tmp_path / "sub2"
    sub1.mkdir()
    sub2.mkdir()

    (sub1 / "a.py").write_text("tax = price * 0.15\n", encoding="utf-8")
    (sub2 / "b.py").write_text("is_admin = role == 'admin'\n", encoding="utf-8")

    report = nesr_logic.scan(tmp_path)
    assert len(report.records) == 2
    assert report.records[0].id == "LOG-0001"
    assert report.records[1].id == "LOG-0002"
    files = {r.file for r in report.records}
    assert len(files) == 2


def test_json_serialization(tmp_path: pathlib.Path):
    """Test 16: JSON serialization."""
    f = tmp_path / "mod.py"
    f.write_text("discount = price * 0.2\n", encoding="utf-8")

    report = nesr_logic.scan(f)
    json_str = report.to_json()
    data = json.loads(json_str)

    assert "target" in data
    assert "summary" in data
    assert "records" in data
    assert len(data["records"]) == 1
    rec_data = data["records"][0]
    assert rec_data["id"] == "LOG-0001"
    assert "Business Logic" in rec_data["category"]
    assert rec_data["outputs"] == ["discount"]


def test_python_310_compatibility():
    """Test 17: Python 3.10+ compatibility."""
    assert sys.version_info >= (3, 10), "Requires Python >= 3.10"
    # Ensure dataclasses asdict and type annotations work
    rec = nesr_logic.LogicRecord(
        id="LOG-0001",
        category=["Boolean Logic"],
        description="Test",
        file="test.py",
        line_start=1,
        line_end=1,
        expression="a and b",
        inputs=["a", "b"],
        outputs=[],
        inferred_types={},
        dependencies=[],
        is_annotated=False,
        detection_method="ast_heuristic",
        confidence="medium",
        warnings=[],
    )
    d = rec.to_dict()
    assert d["id"] == "LOG-0001"


def test_no_execution_of_scanned_code(tmp_path: pathlib.Path):
    """Test 18: Scanned source code must NEVER be executed."""
    # If this code were executed, it would create a side-effect file and raise an error.
    trap_file = tmp_path / "trap_executed.txt"
    malicious_code = f'''
import pathlib
pathlib.Path(r"{trap_file}").write_text("EXPLODED")
raise SystemExit("MALICIOUS CODE EXECUTED!")
'''
    f = tmp_path / "trap.py"
    f.write_text(malicious_code, encoding="utf-8")

    report = nesr_logic.scan(f)
    # The side-effect file must NOT exist
    assert not trap_file.exists(), "SECURITY BREACH: Scanned source code was executed!"


def test_cli_interface(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture):
    """Test CLI commands and flags."""
    f = tmp_path / "app.py"
    f.write_text("# (L)\naccess = role == 'admin'\n", encoding="utf-8")

    # CLI scan text format
    rc = nesr_logic.main(["scan", str(f)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "NESR Logic Scan Report" in captured.out
    assert "[ANNOTATED] LOG-0001" in captured.out

    # CLI scan json format
    rc = nesr_logic.main(["scan", str(f), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["summary"]["explicit_annotated"] == 1

    # CLI scan strict mode on unannotated
    unannot = tmp_path / "unannot.py"
    unannot.write_text("x = y > 10\n", encoding="utf-8")
    rc_strict = nesr_logic.main(["scan", str(unannot), "--strict"])
    assert rc_strict == 1
