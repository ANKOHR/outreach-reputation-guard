# Local build evidence

Measured on 2026-10-01 on this Windows workspace, Python 3.12.10, pytest 8.3.5. CPU only. No model calls, network functionality, or GPU dependencies are present in the tool.

- `python -m pytest -q`: 32 passed in 1.48 seconds.
- Installed `org` execution: fixture generation, full run, and Markdown report written to `demo/report.md` completed in 0.8391356 seconds, measured with a PowerShell Stopwatch. This is measured runtime, not measured time saved.
- The exact three-command demo with report stdout captured locally completed in 0.8229459 seconds.
- Synthetic 200-record ground truth: 140 approved, 60 blocked; 20 low scores and 10 each suppressed, no permission, duplicate recipient, and daily cap. All decisions and reason counts equal the independently enumerated expectations.
- Synthetic false positives and false negatives: zero, checked by comparing the complete blocked-ID sets with planted ground truth.
- Corruption experiment: changing synthetic record 140's score from 20 to 90 changes low-score count from 20 to 19 and cap count from 10 to 11. Totals remain 140 approved and 60 blocked because the supplied capacity is already exhausted. This proves reason counts respond to input changes.
- Adversarial checks cover negative values, future and invalid dates, duplicate IDs, extreme strings, Unicode, Windows path strings, schema drift, malformed JSON, missing paths, an empty directory, and report write failures with no partial temporary files.
- Repeat run output and saved state are byte-identical. Every report includes declared provenance and explicitly unmeasured savings.

No real outreach trial was performed. Scores, permissions, and declared prior-send counts have not been independently validated. No real adoption, financial benefit, or reputation effect is claimed. Final verdict is pending the real-use evidence window described in README and VERDICT.md.
