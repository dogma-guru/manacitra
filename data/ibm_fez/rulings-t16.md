# Test 16: the readings put to the author before the go

After the rule's hash check and the hash checks that open nothing, and before any array was opened, the runner listed six readings in the runner's chat. At each one the rule leaves a choice. The author's go followed at 2026-10-19T12:15:33Z (UTC), "19 October 2026 (UTC); issue 67", with no objection and no separate ruling. The runner applied the readings as stated below. The rule was not changed; these fix how its words are applied where it leaves a choice.

1. **Test 15's code.** Test 15's definitions are applied by test 15's own `read_t15.py`, imported unchanged (its SHA-256 `8f8d5094…62003147` equals its line in `tests/handback/t15/SHA256SUMS`). Only its hand-back root is pointed at `tests/handback/`.
2. **The scorer's command.** It runs once as `python -I -B` from `tests/handback/t16/`. The `<array>`, `<meta>` and `<counts>` slots get paths into `../t11-day3/`. The predictions file is given by its path in the scorer folder. `--out scorecard-t16.json` stays as written. The scorer appends its own `data-run.log` in its folder, which is its own behaviour; none of its files is edited.
3. **The borrowed τ_c for job 1.** It is the median over the day 3 monitor spans where τ_c is read. A span at the ceiling would be left out and listed. If no span had a read τ_c, the runner would stop and ask.
4. **The day mean duties.** Each day's mean is taken over its six spans on w's branch. Each day's sd is the root sum of squares of its spans' sd over six, which is test 15's job mean recipe. If the branch differed between days, the runner would stop and ask.
5. **The middle span minus the end spans.** This is given for all four monitor jobs, day 2's two from `fits-t15.json` and day 3's two from this read, on the duty b, labelled not a test.
6. **Sensitivity.** It is given for the four boundary words and for the between jobs word. Job 1's borrowed words get none, as in test 15.

None of the contingencies in 3 and 4 arose: all six day 3 monitor spans have a read τ_c, and every span on both days is on the branch b.
