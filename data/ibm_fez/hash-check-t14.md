# Hash check, test 14

The author named the public issue, issue 62 of the public repository, and pasted its body, which gives the SHA-256 of `t14-rule.md` as

`0a75dd452264102f91845da08bfe0ff341c0403f651896cafafe612e0e6a4d4b`

The issue was read directly from GitHub at 2026-10-18T01:33Z: issue 62, open, created 2026-10-18T01:30:56Z, titled "Test 14: fixed before the run (SHA-256)". Its body carries the same digest.

The runner computed the digest of `tests/t14-fez-143-in-phase-control/t14-rule.md` with `shasum -a 256` at 2026-10-18T01:33:29Z:

`0a75dd452264102f91845da08bfe0ff341c0403f651896cafafe612e0e6a4d4b`

The file `t14-rule.sha256` beside it carries the same digest.

Result: MATCH. The rule was public before the job was built.
