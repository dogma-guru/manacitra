# Redaction log

Final search of every file in the hand-back, with the patterns of probe 02's final search: account numbers, arn:aws strings carrying one, access keys, bucket names, email addresses, the working folder's name, the profile name, home paths, and the account's spending figures for this device (read with one read call and written nowhere). Each file was also searched when it was first saved in the working folder; that log is `raw-redaction-log.md`.

The spending limit's field names are not searched in `.py` files, as probe 02 dated on 21 October 2026 (its `go.log` and the comment in `scripts/finalize.py`): a field name in source is not a figure. The figures themselves are searched in every file, scripts included.

## Matches explained and kept

Kept at the author's ruling of 21 October 2026. The matched text and the pattern that matched are not written here. The scripts are as run: not edited, not excluded from the search.

| UTC | file | line | action | reason |
|---|---|---|---|---|
| 2026-10-21T20:59:27Z | scripts/run_probe-probe02-start.py | 51 | explained, kept | a code constant (ten minutes in seconds, or a file mode), not a spending figure |
| 2026-10-21T20:59:27Z | scripts/run_probe-probe02-start.py | 238 | explained, kept | a code constant (ten minutes in seconds, or a file mode), not a spending figure |
| 2026-10-21T20:59:27Z | scripts/run_probe-probe02-start.py | 316 | explained, kept | a code constant (ten minutes in seconds, or a file mode), not a spending figure |
| 2026-10-21T20:59:27Z | scripts/run_probe.py | 55 | explained, kept | a code constant (ten minutes in seconds, or a file mode), not a spending figure |
| 2026-10-21T20:59:27Z | scripts/run_probe.py | 220 | explained, kept | a code constant (ten minutes in seconds, or a file mode), not a spending figure |
| 2026-10-21T20:59:27Z | scripts/run_probe.py | 398 | explained, kept | a code constant (ten minutes in seconds, or a file mode), not a spending figure |

## Every file

Apart from the 6 matches above, the same search over every file in the hand-back found nothing to redact. Rows marked "not redacted" are the search's own recorded exceptions (fraction digits of a published figure; a run of twelve digits inside a SHA-256 hash).

| UTC | file | kind | count | action |
|---|---|---|---|---|
| 2026-10-21T20:59:27Z | braket-probe-03-program-set-rule.md | none found | 0 | none |
| 2026-10-21T20:59:27Z | go.log | none found | 0 | none |
| 2026-10-21T20:59:27Z | pre-go-checks.md | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/README.md | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/filled.sha256 | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/task-E1.qasm | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/task-E2.qasm | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/template-E1.qasm | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/template-E2.qasm | none found | 0 | none |
| 2026-10-21T20:59:27Z | programs/templates.sha256 | none found | 0 | none |
| 2026-10-21T20:59:27Z | raw/creation-error.txt | none found | 0 | none |
| 2026-10-21T20:59:27Z | raw/device-meta-presubmission-20261021T203820Z.json | none found | 0 | none |
| 2026-10-21T20:59:27Z | raw/program-set-ir.json | none found | 0 | none |
| 2026-10-21T20:59:27Z | raw/properties-presubmission-20261021T203820Z.json | 12-digit run after a decimal point (a figure's fraction digits) | 3 | not redacted |
| 2026-10-21T20:59:27Z | raw-redaction-log.md | none found | 0 | none |
| 2026-10-21T20:59:27Z | report-probe-03.md | none found | 0 | none |
| 2026-10-21T20:59:27Z | rule.sha256 | none found | 0 | none |
| 2026-10-21T20:59:27Z | run-log.json | none found | 0 | none |
| 2026-10-21T20:59:27Z | run-stdout.log | none found | 0 | none |
| 2026-10-21T20:59:27Z | run.log | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/check_limit.py | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/check_window.py | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/common-probe02-start.py | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/common.py | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/explain_kept.py | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/finalize.py | none found | 0 | none |
| 2026-10-21T20:59:27Z | scripts/run_probe-probe02-start.py | 12-digit run inside a SHA-256 hash | 1 | not redacted |
| 2026-10-21T20:59:27Z | sdk-program-set-notes.md | none found | 0 | none |

Order: this log was made final at 2026-10-21T20:59:27Z; `SHA256SUMS` was then written over every file in the hand-back, this log included, and searched in turn.
