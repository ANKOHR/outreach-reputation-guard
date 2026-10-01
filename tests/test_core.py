import copy
import pytest
from outreach_reputation_guard.core import GuardError, evaluate
from outreach_reputation_guard.fixtures import fixture_data


@pytest.mark.parametrize("field,value", [("score", -1), ("score", 101), ("score", True), ("date", "2026-10-01"), ("date", "invalid"), ("recipient", "x" * 10001), ("permission", "yes"), ("id", "")])
def test_rejects_adversarial_values(field, value):
    policy, rows, _ = fixture_data()
    rows[0][field] = value
    with pytest.raises(GuardError, match=field):
        evaluate(policy, rows)


def test_duplicate_ids_rejected():
    policy, rows, _ = fixture_data()
    rows[1]["id"] = rows[0]["id"]
    with pytest.raises(GuardError, match="duplicate id"):
        evaluate(policy, rows)


@pytest.mark.parametrize("field", ["daily_limit", "already_sent", "min_score"])
def test_negative_policy_rejected(field):
    policy, rows, _ = fixture_data()
    policy[field] = -1
    with pytest.raises(GuardError, match=field):
        evaluate(policy, rows)


def test_handles_unicode_and_long_inputs():
    policy, rows, _ = fixture_data()
    rows[0]["recipient"] = "C:\\用户\\café\\" + "長" * 9000
    rows[0]["id"] = "用户-é"
    assert evaluate(policy, rows)["decisions"][0]["allowed"]


def test_multiple_reasons_and_stale_date():
    policy, rows, _ = fixture_data()
    rows[0].update(date="2026-09-29", score=0, suppressed=True, permission=False)
    assert evaluate(policy, rows)["decisions"][0]["reasons"] == ["stale_date", "low_score", "suppressed", "no_permission"]


def test_supplied_baseline_consumes_capacity():
    policy, rows, _ = fixture_data()
    policy["already_sent"] = 140
    assert evaluate(policy, rows)["totals"]["allowed"] == 0


def test_schema_drift():
    policy, rows, _ = fixture_data()
    rows[0]["amount"] = -1
    with pytest.raises(GuardError, match="amount"):
        evaluate(policy, rows)
