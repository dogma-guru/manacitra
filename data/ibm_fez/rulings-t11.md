# Test 11: the author's rulings before the go

Asked by the runner and answered by the author in the runner's chat at about 2026-10-17T19:50Z (UTC), after the hash check and before any job was built. The rule was not changed; these fix how its words are applied where they could be read in more than one way.

1. **Job 1's fit seeds.** The rule names the interleaving seed 11301 and the bootstrap seed 11304 and says "the same fits". Ruling: the other seeds stay test 7's. Job 1 uses S starts 7302, P random starts 7303, bootstrap 11304, T random starts 7305, periodogram noise 7306.
2. **The job's median phase (step 6).** Angles are circular. Ruling: the median of the θ_k, each wrapped to within π of their circular mean (the median taken on one sheet of the circle). The circular mean, the reading of Mantri's desk check, is computed beside it, and any repeat whose branch differs between the two readings is listed.
   - Before the ruling, the runner's synthetic check (`synth_t11.py`, 100 trials per case) met every required rate under either reading.
   - The two readings differed on one case that carries no required weight rate. With a 40 kHz common step, the weight read WEIGHT SWITCHES WITHIN SPANS in 66 of 100 trials under the median and WEIGHT QUIET in 100 of 100 under the circular mean. This was put to the author with the question.
3. **Job 1's weight change across a span boundary (the counts of the run).** The change is read from the nearest three positions passing the lever on each side. Ruling: the change is the plain mean of the three after minus the plain mean of the three before. On day 1 this reads 0.160 at the first boundary and 0.031 at the second.
