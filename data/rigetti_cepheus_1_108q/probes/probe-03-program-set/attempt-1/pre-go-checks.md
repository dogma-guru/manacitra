# Checks before the go, 21 October 2026 (UTC)

Read calls only. Nothing was submitted.

| UTC | check | result |
|---|---|---|
| 2026-10-21T20:30:31Z | rule copied unchanged | SHA-256 b9748919eb26918976fbfd4ff0028899294cffbc97975e1cb6167e570811fb27, in `rule.sha256` |
| 2026-10-21T20:35:41Z | spending limit for this device | one limit; its period covers today; what remains covers [cost]. The account's figures are not recorded here. |
| 2026-10-21T20:35:41Z | price list estimate, one task of 200 shots (the Tracker's own lookup) | [cost] |
| 2026-10-21T20:35:48Z | device status | ONLINE; queue Normal 0, Priority 0 |
| 2026-10-21T20:35:48Z | availability window | inside the 16:00:00 to 23:59:59 window; 12251 s left; published windows equal the runner's |
| 2026-10-21T20:35:48Z | program-set action in the properties | `braket.ir.openqasm.program_set`, version 1, maximumExecutables 100, maximumTotalShots 200000 |

The SDK reading is in `sdk-program-set-notes.md`. The guard was tested offline against a stubbed service (no network):
ten wrong calls refused, one call of the right shape sent once, the second run refused.
