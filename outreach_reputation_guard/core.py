"""Pure decisions from supplied facts. Savings are unmeasured, never estimated."""
from collections import Counter
from datetime import date


class GuardError(ValueError):
    """Named input or output failure."""


def fail(field, message):
    raise GuardError(f"SchemaError: {field}: {message}")


def fields(value, expected, field):
    if not isinstance(value, dict):
        fail(field, "expected object")
    for key in sorted(set(value) ^ set(expected)):
        fail(f"{field}.{key}", "missing or unknown field")


def day(value, field):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError()
        return date.fromisoformat(value)
    except ValueError:
        fail(field, "expected ISO date YYYY-MM-DD")


def evaluate(config, records):
    fields(config, {"synthetic", "as_of", "daily_limit", "already_sent", "min_score"}, "policy")
    if type(config["synthetic"]) is not bool:
        fail("policy.synthetic", "expected boolean")
    as_of = day(config["as_of"], "policy.as_of")
    for key in ("daily_limit", "already_sent", "min_score"):
        if type(config[key]) is not int or config[key] < 0:
            fail(f"policy.{key}", "expected nonnegative integer")
    if config["min_score"] > 100:
        fail("policy.min_score", "must be <= 100")
    seen_ids, recipients = set(), set()
    decisions, reasons = [], Counter()
    allowed = 0
    for index, row in enumerate(records):
        prefix = f"records[{index}]"
        fields(row, {"id", "recipient", "date", "score", "permission", "suppressed", "synthetic"}, prefix)
        for key in ("id", "recipient"):
            if not isinstance(row[key], str) or not row[key].strip() or len(row[key]) > 10000:
                fail(f"{prefix}.{key}", "expected nonempty string of at most 10000 characters")
            if "\u2014" in row[key]:
                fail(f"{prefix}.{key}", "em dash is prohibited")
        if row["id"] in seen_ids:
            fail(f"{prefix}.id", "duplicate id")
        seen_ids.add(row["id"])
        for key in ("permission", "suppressed", "synthetic"):
            if type(row[key]) is not bool:
                fail(f"{prefix}.{key}", "expected boolean")
        if type(row["score"]) is not int or not 0 <= row["score"] <= 100:
            fail(f"{prefix}.score", "expected integer 0..100")
        scheduled = day(row["date"], f"{prefix}.date")
        if scheduled > as_of:
            fail(f"{prefix}.date", "future date relative to policy.as_of")
        key = row["recipient"].strip().casefold()
        blocked = []
        if scheduled != as_of:
            blocked.append("stale_date")
        if row["score"] < config["min_score"]:
            blocked.append("low_score")
        if row["suppressed"]:
            blocked.append("suppressed")
        if not row["permission"]:
            blocked.append("no_permission")
        if key in recipients:
            blocked.append("duplicate_recipient")
        recipients.add(key)
        if not blocked and config["already_sent"] + allowed >= config["daily_limit"]:
            blocked.append("daily_cap")
        if not blocked:
            allowed += 1
        reasons.update(blocked)
        decisions.append({"id": row["id"], "allowed": not blocked, "reasons": blocked})
    synthetic = sum(row["synthetic"] for row in records)
    return {"policy": config, "totals": {"records": len(records), "allowed": allowed,
            "blocked": len(records) - allowed, "synthetic_records": synthetic,
            "real_records": len(records) - synthetic}, "reason_counts": dict(sorted(reasons.items())),
            "decisions": decisions, "savings": {"status": "unmeasured", "value": None}}
