# Round 5c of the desk power check: version 5.1's grid on a second machine

Round 5c ran the power check of test 7's rule again, on a second machine, with the same script and the same seeds as round 5b ([`../t7-power-check/`](../t7-power-check/README.md)), from 16 to 18 October 2026, and set its draws beside round 5b's point for point and draw for draw. It is published beside round 5b by the author's answer of 19 October 2026 (Amendment A28). Like round 5b, it simulates the two models of the rule with binomial shot noise; it is not a measurement of any device.

**What the two result files show,** counted again here from round 5b's results, attached to the 0.8.0 release, and round 5c's, to be attached to the 0.10.0 release. KEPT on both machines: 106 of the 117 counted points return the generating verdict in at least 80% of draws, where 88 were needed. 8 of the 27,000 draws differ in verdict, all at τ = 150 µs and δ = 30 kHz, each traced to a P fit in a distant minimum on one machine (P's χ² of 10,614 to 19,473 there, against 44 to 75 on the other). At the two points with lines at 25 and 125 kHz, 393 draws differ in S's held-out error by whole numbers of counts, multiples of 1/192,000 (64 held-out points of 3,000 shots), while every χ² agrees to 3·10⁻⁶. There the true probability is exactly one half at six held-out waits (5, 15, 25, 35, 45 and 55 µs); in floating point it falls a rounding error to one side of one half, where the sampler mirrors the count, and a gap of whole counts is what falling on opposite sides on the two machines gives. No verdict moved: at those two points every draw returns the same verdict on both machines, and no point passes the 80% test on one machine and fails it on the other.

The report beside this file, written before that explanation, calls these gaps a fact not traced; the third sentence above is the trace, made from the two result files after the report. Its sentence that the simulated data are the same on both machines rests on S's χ² over the fitted waits; at the two points named above the held-out counts differ, as the third sentence says.

**The files.** Each was checked against the round's `SHA256SUMS` before it was copied. The round's names carried the second machine's name; here they carry "round5c", and in the text the machine is written "the second machine" (the author's ruling of 19 October 2026), with the name of the author's working folder written "[the private working folder]" once in the environment record. Nothing else in any file changed. Each file's SHA-256 as handed back and as published:

| file | what | as handed back | as published |
|---|---|---|---|
| `report-t7v51-round5c.md` | the runner's report: the two machines, the comparison, the run on the second machine, the tables | `c68cc6b8f668cb2d06ba718e5177c06453eb068d88d06ea7efbbcca1d23a9bbb` | `bb5127974b20729215c6d627913b96146852091dc8ba36c7828d253678019efb` |
| `round5c-environment.txt` | the second machine's environment record: platform, Python and libraries, the copy of the repository, the workers | `465256e9291d136817d067244ecaf3091a0f0cee288399efef591be786a4843b` | `e8df83e034668598dfbc8059e5d3e4824a27746e0cdb64c2738f8986a402d1d2` |
| `compare_t7v51_round5c.py` | the comparison script: it reads the two result files and nothing else | `cfe2fb7f3f18a5261976fde5614a773fadef5d8d25849060bab67555756d5c86` | `fa51e8c59801394f8922fbe7de1fbd2d5e43c61e4e029207879dd96c5a667bcd` |
| `compare-t7v51-round5c.json` | its output: every point, and every draw whose verdict differs | `20d116af1cc89c7a9e39d73686b3365f3d0f7cf506512982a7b38f801219f194` | `b738c5742b2b65ed0e7c4bd7d5e7f0246cee6a844de2c7e63ade586b106e0fe5` |
| `tables_t7v51_round5c.py` | the side-by-side tables, from the two result files | `5294fcb5a3e9df1d7161836ca8f03e4fef24dd849cb77da9c8f4eec4a7b41c9b` | `8080b37f49606d90b6aa1c9141b69df7597bc65e358820ab5253e9cdb3a515ec` |
| `tables-t7v51-on-round5c-draws.md` | round 5b's `tables_t7v51.py`, run unchanged on round 5c's draws | `a07499d4e377256a43d383e73ce9e35dfefa549494bb35ee3e0543a8d036f747` | the same |

**The script as run** is round 5b's, byte for byte: `power_t7v51.py`, SHA-256 `663280741fe5dcb6728e4bca5ef55afc759dac5823225b02981bd88929e4b41a`, run by a wrapper on the second machine. Its published copy beside round 5b differs from it in its docstring's first line only ([`../t7-power-check/README.md`](../t7-power-check/README.md)).

**The grid's results** (`results-t7v51-round5c.jsonl`, one line per grid point with all 200 draws; 21,974,276 bytes, renamed and otherwise as handed back) are not in this repository. They are to be attached to the 0.10.0 release as an asset, with this SHA-256:

`f37ca5ccb03e9a3d22b62a17011a32d8296892624d5ae0866c7ba5f9d7f9dd45`

Round 5b's are attached to the 0.8.0 release (`27c29bc2c242312ff9b2ab3b22c987263aa2900ebdcf966c24e0fcc1369b1a48`).

**Left out,** as run control rather than records: the battery guard that paused and resumed the workers by the battery's current, in three versions, with its log and its summary; the wrapper that ran the script on the second machine; its start and status commands; and the grid's run log. Their SHA-256 as handed back:

- the battery guard, versions 1 to 3: `3a28eae748e65952f5895c55f19da3d869e991c4c8817dee770ead73d3928b33`, `cd41a27d5ab43e67be5eb08033469275b29945c8a1f4d22256d308fda5d92bc7`, `ac4ff748fabdb015bee7a85bb1fbdc32abd4dbe61e213f6e7fedd521cc0a86b5`;
- its log and its summary: `3f1b9b3d64c6108b2c620ef358a9d59caa02a624d8dfcade8a438e1ffcd52895`, `84b18d2213908c1e68fa63393a16a913e23c9972e30e3fbdf4f8ebb299b5513a`;
- the wrapper: `10b8664c532e3ce6f4ed8dd3098dd982015c0fa29127d9a49d4cb4fd201572cf`;
- the start and status commands: `a7eda1108f192d555b882c76f3d4b2c9c49a075d398f4f53961a43d2a8fa75e9`, `675fb2d492b85e2245d8c42d5777f2fb958e29669a99ad1489ec9cdeeb8f31e8`;
- the grid's run log: `2eb4ad3a70bccb01d34ccadad2997b5932678202a39960cc4b4fe6a07f53afcf`.

**Rerunning the comparison.** From a folder holding both result files: `python compare_t7v51_round5c.py results-t7v51-round5c.jsonl results-t7v51.jsonl compare-t7v51-round5c.json`, then `python tables_t7v51_round5c.py results-t7v51-round5c.jsonl results-t7v51.jsonl`.
