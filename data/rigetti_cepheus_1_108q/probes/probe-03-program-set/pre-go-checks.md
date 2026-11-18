# Attempt 2: checks before the go, 21 October 2026 (UTC)

Read calls and offline checks only. Nothing was submitted.

| UTC | check | result |
|---|---|---|
| 2026-10-21T21:08:23Z | rule copied again, unchanged | SHA-256 b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27, in `rule.sha256` |
| 2026-10-21T21:08:23Z | programs | attempt 1's `task-E1.qasm` and `task-E2.qasm` copied; both hashes check against attempt 1's `filled.sha256` |
| before 21:10 | serialised set, offline (installed SDK 1.127.3.post0) | saved form hashes to 7b283c57b488513b9cd0a489d8db53e69df6b88aab8befac3a5fb4e6f5ba89d2, equal to attempt 1's `raw/program-set-ir.json`, and equal to that file byte for byte; compact action sent to the service hashes to 9afd5c89507a5873251930fadfd0c1db94de87306b2e91e06f1145503e0a2be8 |
| before 21:10 | guard, offline against a stubbed service | ten wrong calls refused, a changed action below run refused, one call of the right shape sent once, the second run refused |
| 2026-10-21T21:10:48Z | spending limit for this device | one limit; its period covers today; what remains covers [cost]. The account's figures are not recorded here. |
| 2026-10-21T21:10:48Z | price list estimate, one task of 200 shots | [cost] |
| 2026-10-21T21:10:50Z | device status | ONLINE; queue Normal 0, Priority 0 |
| 2026-10-21T21:10:50Z | availability window | inside the 16:00:00 to 23:59:59 window; 10149 s left; published windows equal the runner's |
| 2026-10-21T21:10:50Z | program-set action in the properties | unchanged from attempt 1: version 1, maximumExecutables 100, maximumTotalShots 200000 |
