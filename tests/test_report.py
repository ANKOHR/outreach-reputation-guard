import json
from outreach_reputation_guard.cli import load_input
from outreach_reputation_guard.report import render


def test_report_matches_ground_truth_exact(fixture_dir):
    report = json.loads(render(load_input(fixture_dir), "json"))
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    for key in ("totals", "reason_counts", "decisions"):
        assert report[key] == expected[key]


def test_report_zero_false_positives(fixture_dir):
    result = load_input(fixture_dir)
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    actual_blocks = {row["id"] for row in result["decisions"] if not row["allowed"]}
    planted_blocks = {row["id"] for row in expected["decisions"] if not row["allowed"]}
    assert actual_blocks == planted_blocks


def test_report_carries_provenance_banner(fixture_dir):
    result = load_input(fixture_dir)
    for format in ("md", "json"):
        output = render(result, format)
        assert "Data provenance:" in output
        assert "200 synthetic fixture records" in output
        assert "0 real records" in output


def test_hypothetical_figures_labelled(fixture_dir):
    result = load_input(fixture_dir)
    assert result["savings"] == {"status": "unmeasured", "value": None}
    assert "unmeasured" in render(result)
    assert "not predicted" in render(result)


def test_no_em_dashes_in_outputs(fixture_dir):
    for format in ("md", "json"):
        assert chr(0x2014) not in render(load_input(fixture_dir), format)
