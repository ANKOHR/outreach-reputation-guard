"""Deterministic reporting with provenance and explicit measurement boundaries."""
import json


def render(result, format="md"):
    totals = result["totals"]
    banner = (f"Data provenance: {totals['synthetic_records']} synthetic fixture records; "
              f"{totals['real_records']} real records declared by the input author (Henry's own hand-entered data when supplied by Henry). "
              f"Policy: {'synthetic' if result['policy']['synthetic'] else 'real, author-declared'}. "
              "Provenance is a declaration, not independently verified.")
    if format == "json":
        return json.dumps({"provenance_banner": banner, **result}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lines = ["# Outreach Reputation Guard", "", banner, "", "Computed input decisions, not predicted deliverability or measured sending outcomes.", "", "| Count | Value |", "| --- | ---: |"]
    lines.extend(f"| {key} | {value} |" for key, value in totals.items())
    lines += ["", "## Block reasons", "", "Counts can overlap when a record has multiple reasons."]
    lines.extend(f"- {key}: {value}" for key, value in result["reason_counts"].items())
    lines += ["", "Time saved and money saved: unmeasured; no estimate reported.", "", "## Decisions", "", "```json", json.dumps(result["decisions"], ensure_ascii=False, sort_keys=True, indent=2), "```", ""]
    return "\n".join(lines)
