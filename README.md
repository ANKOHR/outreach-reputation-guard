# Outreach Reputation Guard

`org` computes deterministic send approvals from explicit local inputs. It prevents excessive or low-quality sending by producing an approval list for Henry to use before sending. It never sends messages or predicts delivery, replies, reputation, legal compliance, revenue, or qualification quality. A score and permission flag are supplied facts, not facts this tool discovers.

## Quickstart

Python 3.10 or later, CPU only, no runtime dependencies. From the repository:

```powershell
python -m pip install --no-deps --no-build-isolation -e .
org fixtures --out demo
org run --input demo
org report --format md
python -m pytest -q
```

The demo generates 200 synthetic records and computes all decisions. The JSON expectations file is an independent, hand-computed oracle; the engine does not read it. The generated fixture contains 140 approvals and 60 blocks: 20 low scores, 10 suppressions, 10 missing permissions, 10 duplicate recipients, and 10 daily-cap blocks. These are synthetic counts, not measured outreach outcomes. No randomness is used, so no seed is needed. Same input and policy give identical output bytes; input array order is part of the policy.

If pip reports its Scripts directory is outside PATH, add the directory it prints to your session PATH or use `python -m outreach_reputation_guard.cli` in place of `org`. Installation uses local setuptools and no dependency downloads. Tests require pytest already installed.

## Input format

An input directory contains `policy.json` and `records.json`, UTF-8 JSON. Other files, including `expectations.json`, are ignored. CSV and YAML are not supported. JSON cannot contain header comments: synthetic JSON files carry `synthetic: true` and the accompanying `SYNTHETIC.md` has a header comment. Every record has an explicit provenance flag. Setting the flag to false declares real data; it does not authenticate the author or verify its truth.

Policy example (illustrative synthetic policy, not a recommended sending threshold):

```json
{"synthetic": true, "as_of": "2026-09-30", "daily_limit": 2, "already_sent": 0, "min_score": 70}
```

Small hand-written five-record synthetic example for `records.json`:

```json
{
  "synthetic": true,
  "label": "SYNTHETIC hand-written example",
  "records": [
    {"id":"a","recipient":"a@example.test","date":"2026-09-30","score":90,"permission":true,"suppressed":false,"synthetic":true},
    {"id":"b","recipient":"b@example.test","date":"2026-09-30","score":90,"permission":true,"suppressed":false,"synthetic":true},
    {"id":"c","recipient":"c@example.test","date":"2026-09-30","score":10,"permission":true,"suppressed":false,"synthetic":true},
    {"id":"d","recipient":"d@example.test","date":"2026-09-30","score":90,"permission":true,"suppressed":true,"synthetic":true},
    {"id":"e","recipient":"e@example.test","date":"2026-09-30","score":90,"permission":true,"suppressed":false,"synthetic":true}
  ]
}
```

That example computes two approvals and three blocks. To try real input, Henry enters his own facts and marks their flags and the policy provenance appropriately. Real trial data and trial results should remain local, outside the tracked repository. Mixed record provenance is supported with container `synthetic: false`; a synthetic container cannot contain real records.

| Field | Rule |
| --- | --- |
| policy.as_of | Explicit ISO date, used instead of the system clock |
| policy.daily_limit | Nonnegative integer cap across already sent plus this approved queue |
| policy.already_sent | Nonnegative integer, author-supplied count for as_of |
| policy.min_score | Integer 0..100, author-supplied threshold |
| id | Unique, nonempty string, up to 10000 characters |
| recipient | Nonempty string, up to 10000 characters; stripped and casefolded for duplicate checks |
| date | ISO date; future dates relative to as_of are errors; older dates are blocked as stale |
| score | Integer 0..100, supplied qualification score |
| permission | Boolean supplied permission to contact, not a legal determination |
| suppressed | Boolean supplied do-not-contact status |
| synthetic | Required boolean on policy, container, and each record |
| label | Required string on records container |

Unknown or missing fields are schema errors. Negative counts, negative scores, boolean counts, duplicate IDs, invalid dates, future dates, and extreme strings are rejected as a whole batch, with no silent omissions. Em dashes in identifiers and recipients are rejected. Unicode and Windows path strings otherwise work. Duplicate recipients refer to any earlier record in this queue, including earlier blocked records. No contact history is inferred across runs. All quality reasons are collected; daily cap applies only to otherwise eligible records. Reason counts can overlap, while allowed plus blocked always equals records.

An empty directory produces a zero report with an explicit placeholder policy (`2000-01-01`, zero thresholds and counts). A nonempty directory missing required files is an error. The tool does not reserve slots across runs: `already_sent` must be updated by the operator. Concurrent runs do not coordinate, so approval is a review gate, not an enforced sending service.

## Commands

| Command | Example and purpose |
| --- | --- |
| fixtures | `org fixtures --out demo`: generate labelled synthetic fixture files, overwriting same-name files |
| run | `org run --input demo --state .org/results.json`: compute and atomically save decisions |
| report | `org report --format md`: render latest saved results |
| report | `org report --input demo --format json --out report.json`: compute and atomically write a report |
| screen | `org screen --input demo`: show all qualification, suppression, duplicate, and capacity decisions |
| budget | `org budget --input demo`: show computed capacity remaining after the approved queue |

Every command supports `--help` and examples. Run, screen, and budget show provenance. `report` defaults to `.org/results.json`; `--state` selects another saved file. Failed runs leave the previous state unchanged; only use results after a successful run. Errors exit 2 with named `ParseError`, `SchemaError`, `MissingInput`, `InputError`, or `WriteError`. Parse errors identify the filename and line. Schema errors identify the offending field. Report writes use a temporary file and atomic replacement, cleaning temporary files on failure. The report lists each record ID and reasons so figures can be traced to inputs.

## Architecture

```text
fixtures.py -> labelled local JSON + independent expectations
local JSON -> cli.py validation -> core.py pure evaluation
                                  -> report.py JSON / Markdown
                                  -> atomic local result file
pytest -> planted oracle, adversarial input, CLI and provenance checks
```

## Honesty boundary

All totals are computed from supplied records and policy. Synthetic data is labelled inside each fixture file and in every report banner. Real data provenance is author-declared, never independently verified. Permissions, scores, dates, and prior sends can be incorrect if entered incorrectly. Fixture accuracy measures implementation against planted rules, not accuracy of Henry's real-world qualification. Time and money saved are unmeasured, with a null value and explicit label; no hypothetical savings or predicted outcomes are reported. The illustrative policy and five-record example above are explicitly synthetic. Runtime measurements in `EVIDENCE.md` measure this local demo, not time saved against a baseline.

## Evidence-based improvement hook and verdict

The two-week window starts with Henry's first real use, not the build date. Keep a local trial log with run date, whether used, sample size, hand-checked approve/block decisions, disagreements, and top disagreement cause. Measure decision error rate = disagreements / hand-checked decisions. A zero-sized sample is unmeasured, not zero error. After two weeks, if error rate exceeds 10 percent, fix the top failure cause and remeasure or kill with a recorded reason. If unused, record that fact and kill. Do not ship the real trial log.

The final verdict is pending that evidence window; no usage or revenue is invented. Record the dated reason in `VERDICT.md`: expand if daily use or revenue is established, integrate if there is heavy sibling-project overlap, commercialise if a buyer would pay as-is, maintain as portfolio evidence otherwise, or kill if unused or acceptance criteria cannot be met.

See `EVIDENCE.md` for build verification and `LESSONS.md` for build lessons. Public publishing is authorised but handled separately, not by this build.
