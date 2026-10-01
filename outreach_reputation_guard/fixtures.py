"""Synthetic labelled data with explicitly enumerated planted expectations; no randomness."""
import json
from pathlib import Path


def fixture_data():
    policy = {"synthetic": True, "as_of": "2026-09-30", "daily_limit": 140,
              "already_sent": 0, "min_score": 70}
    records, decisions = [], []
    for i in range(200):
        reason = (None if i < 140 else "low_score" if i < 160 else "suppressed"
                  if i < 170 else "no_permission" if i < 180 else "duplicate_recipient"
                  if i < 190 else "daily_cap")
        records.append({"id": f"lead-{i:03}", "recipient": f"person{i if reason != 'duplicate_recipient' else i - 180}@example.test",
                        "date": "2026-09-30", "score": 20 if reason == "low_score" else 90,
                        "permission": reason != "no_permission", "suppressed": reason == "suppressed", "synthetic": True})
        decisions.append({"id": f"lead-{i:03}", "allowed": reason is None, "reasons": [] if reason is None else [reason]})
    expected = {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth: 140 + 20 + 10 + 10 + 10 + 10 = 200",
                "totals": {"records": 200, "allowed": 140, "blocked": 60, "synthetic_records": 200, "real_records": 0},
                "reason_counts": {"low_score": 20, "suppressed": 10, "no_permission": 10, "duplicate_recipient": 10, "daily_cap": 10},
                "decisions": decisions}
    return policy, records, expected


def generate(out):
    path = Path(out)
    path.mkdir(parents=True, exist_ok=True)
    policy, records, expected = fixture_data()
    for name, data in (("policy.json", policy), ("records.json", {"synthetic": True, "label": "SYNTHETIC fixture", "records": records}), ("expectations.json", expected)):
        (path / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (path / "SYNTHETIC.md").write_text("<!-- SYNTHETIC -->\nAll files in this directory are synthetic fixtures. JSON carries synthetic: true instead of invalid JSON comments.\n", encoding="utf-8")
