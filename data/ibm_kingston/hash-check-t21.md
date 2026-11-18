# Test 21: hash checks

## The rule

| What | UTC time | Digest given by the author (in chat, and as posted in public issue 79) | Digest computed by the runner | Result |
|---|---|---|---|---|
| `t21-rule.md` | 2026-11-17T01:50:54Z | ea1a777b6e910e93b2a898a408fdac7ea023a29112f57732d4c3460764a7035d | ea1a777b6e910e93b2a898a408fdac7ea023a29112f57732d4c3460764a7035d | MATCH |
| `t21-rule.md`, again at the go | 2026-11-17T02:19:40Z | ea1a777b6e910e93b2a898a408fdac7ea023a29112f57732d4c3460764a7035d | ea1a777b6e910e93b2a898a408fdac7ea023a29112f57732d4c3460764a7035d | MATCH |

Computed with `shasum -a 256 t21-rule.md` in `tests/t21-kingston-11-95-look/`. The stored `t21-rule.sha256` carries the same value. The file `t21-rule-DRAFT.md` in the same folder is byte for byte identical to `t21-rule.md`.

Issue 79 ("Test 21: fixed before the run (SHA-256)", created 2026-11-17T01:49:50Z) was read at 2026-11-17T01:51:15Z and carries the digest above. It shows no edit since it was created (updated 2026-11-17T01:49:50Z).

At the go, issue 79 was read again at 2026-11-17T02:19:40Z: it carries the same digest and shows no edit since it was created.
