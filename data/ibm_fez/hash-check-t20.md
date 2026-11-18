# Test 20: hash checks

## The rule

| What | UTC time | Digest given by the author (as posted in public issue 78) | Digest computed by the runner | Result |
|---|---|---|---|---|
| `t20-rule.md` | 2026-11-16T23:12:19Z | 9ea1fded37ecf90a4d9fe468132d6d1ddfb35515fc1f1dbb0b54b90e556af633 | 9ea1fded37ecf90a4d9fe468132d6d1ddfb35515fc1f1dbb0b54b90e556af633 | MATCH |
| `t20-rule.md`, again at the go | 2026-11-17T00:25:42Z | 9ea1fded37ecf90a4d9fe468132d6d1ddfb35515fc1f1dbb0b54b90e556af633 | 9ea1fded37ecf90a4d9fe468132d6d1ddfb35515fc1f1dbb0b54b90e556af633 | MATCH |

Computed with `shasum -a 256 t20-rule.md` in `tests/t20-fez-143-fifth-date/`. The stored `t20-rule.sha256` carries the same value. The file `t20-rule-DRAFT.md` in the same folder is byte for byte identical to `t20-rule.md`.

## Test 18's scorecard, on issue 71 (checked before the go)

| File | UTC time | Digest in the comment on issue 71 (posted 2026-11-15T02:44:02Z) | Digest computed by the runner | Result |
|---|---|---|---|---|
| `tests/handback/t18/scorecard-t18.json` | 2026-11-16T23:14:03Z | 01999991619b1180cbb223514e715a1a6b9ef6a99e8617088227fb4306e3345b | 01999991619b1180cbb223514e715a1a6b9ef6a99e8617088227fb4306e3345b | MATCH |
| `tests/handback/t18/report-t18.md` (beside) | 2026-11-16T23:14:03Z | c89990888253a1a4f07e1119d2abdfae58c9b18c329f630ca59c3388b57f9452 | c89990888253a1a4f07e1119d2abdfae58c9b18c329f630ca59c3388b57f9452 | MATCH |

## Sandhi version 4.1's scorer and predictions (`sandhi-v41-scorer/`, copied from the model's hand-back folder)

| Check | UTC time | Expected | Result |
|---|---|---|---|
| `FORECAST-SHA256SUMS` | 2026-11-16T23:14:03Z | 7903a281…b083 (t20-rule.md section 6) | 7903a281ccc808ed8dd13c4b316919554879ec29a353f7093642c98b9081b083, MATCH |
| the 11 files it lists, `shasum -a 256 -c FORECAST-SHA256SUMS` | 2026-11-16T23:14:03Z | every file OK | 11 of 11 OK |
| `predictions-model-01-v4.1.md` | 2026-11-16T23:14:03Z | 5b2e45de…628f | 5b2e45dea15f613d4314a959d5c06bebf0a663a5f1cb7e607f442ce45b98628f, MATCH |
| `predictions-model-01-v4.1.json` | 2026-11-16T23:14:03Z | a30488be…fc54 | a30488be57eade0df185c594cd83befa5817f8e54261a47423017d0d9814fc54, MATCH |

The copy is byte for byte the same as test 18's copy (`tests/t18-two-monitors-fez-143/sandhi-v41-scorer/`), with the model's `README.md` added.

Issue 78 ("Test 20: fixed before the run (SHA-256)", created 2026-11-16T23:12:05Z) was read at 2026-11-16T23:14:10Z and carries the digest above.

At the go, issue 78 was read again at 2026-11-17T00:25:42Z: it carries the same digest and shows no edit since it was created (updated 2026-11-16T23:12:05Z).
