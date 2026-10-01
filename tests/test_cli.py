import json
import subprocess
import sys
import time
from outreach_reputation_guard.cli import main


def test_run_completes_on_fixture(fixture_dir, tmp_path, capsys):
    start = time.perf_counter()
    state = tmp_path / "state.json"
    assert main(["run", "--input", str(fixture_dir), "--state", str(state)]) == 0
    capsys.readouterr()
    assert main(["report", "--state", str(state)]) == 0
    assert time.perf_counter() - start < 5


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    assert main(["report", "--input", str(tmp_path), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["records"] == 0


def test_malformed_input_named_error(fixture_dir, capsys):
    (fixture_dir / "records.json").write_text('{\n bad json')
    assert main(["run", "--input", str(fixture_dir)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "records.json" in error and "line 2" in error
    assert "Traceback" not in error


def test_determinism_byte_identical(fixture_dir, tmp_path, capsys):
    state = tmp_path / "state.json"
    args = ["run", "--input", str(fixture_dir), "--state", str(state)]
    assert main(args) == 0
    first = state.read_bytes(), capsys.readouterr().out
    assert main(args) == 0
    assert first == (state.read_bytes(), capsys.readouterr().out)


def test_cli_smoke_all_subcommands(tmp_path, capsys):
    path, state = tmp_path / "demo", tmp_path / "state.json"
    assert main(["fixtures", "--out", str(path)]) == 0
    for command in ("run", "screen", "budget"):
        assert main([command, "--input", str(path), "--state", str(state)]) == 0
    for format in ("md", "json"):
        assert main(["report", "--state", str(state), "--format", format]) == 0
    for command in ("fixtures", "run", "screen", "budget", "report"):
        completed = subprocess.run([sys.executable, "-m", "outreach_reputation_guard.cli", command, "--help"], capture_output=True, text=True)
        assert completed.returncode == 0
        assert "Example:" in completed.stdout
    assert chr(0x2014) not in capsys.readouterr().out


def test_missing_input_named_error(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_report_write_failure_no_partial_files(fixture_dir, tmp_path, capsys):
    target = tmp_path / "directory"
    target.mkdir()
    before = set(tmp_path.iterdir())
    assert main(["report", "--input", str(fixture_dir), "--out", str(target)]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert set(tmp_path.iterdir()) == before


def test_handwritten_five_record_real_input(tmp_path, capsys):
    policy = {"synthetic": False, "as_of": "2026-09-30", "daily_limit": 2, "already_sent": 0, "min_score": 70}
    rows = [{"id": str(i), "recipient": f"manual{i}@example.test", "date": "2026-09-30", "score": 90, "permission": True, "suppressed": False, "synthetic": False} for i in range(5)]
    rows[2]["score"] = 10
    rows[3]["suppressed"] = True
    (tmp_path / "policy.json").write_text(json.dumps(policy))
    (tmp_path / "records.json").write_text(json.dumps({"synthetic": False, "label": "Test-only author-declared input, not an actual Henry trial", "records": rows}))
    assert main(["report", "--input", str(tmp_path), "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["totals"]["allowed"] == 2
    assert result["totals"]["blocked"] == 3
