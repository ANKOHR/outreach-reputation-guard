import json
from outreach_reputation_guard.cli import load_input


def test_fixtures_labelled_synthetic(fixture_dir):
    for path in fixture_dir.glob("*.json"):
        assert json.loads(path.read_text(encoding="utf-8"))["synthetic"] is True
    assert "<!-- SYNTHETIC -->" in (fixture_dir / "SYNTHETIC.md").read_text()
    assert all(row["synthetic"] for row in json.loads((fixture_dir / "records.json").read_text())["records"])


def test_fixture_ground_truth_matches_hand_computed(fixture_dir):
    result = load_input(fixture_dir)
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    for key in ("totals", "reason_counts", "decisions"):
        assert result[key] == expected[key]


def test_corrupted_fixture_changes_computed_results(fixture_dir):
    path = fixture_dir / "records.json"
    payload = json.loads(path.read_text())
    payload["records"][140]["score"] = 90
    path.write_text(json.dumps(payload))
    result = load_input(fixture_dir)
    assert result["reason_counts"]["low_score"] == 19
    assert result["reason_counts"]["daily_cap"] == 11
    assert result["decisions"][140]["reasons"] == ["daily_cap"]
