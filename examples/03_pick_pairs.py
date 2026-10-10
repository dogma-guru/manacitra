# Copyright 2026 Dogma LLC
# SPDX-License-Identifier: Apache-2.0
"""The payoff choice, on ibm_fez's archived runs of 5 October 2026.

A map measured first (Kickoff 32, 13:17 UTC) chooses 8 pairs; the published error rates choose another 8. About two
hours later (Kickoff 33, 15:20 UTC) all 27 pairs ran 8 random two-qubit circuits unrelated to the map. Which 8 did
better?
"""

from manacitra import archive
from manacitra.layout import pick_pairs

fez = archive.fez_or_kingston("ibm_fez")
k31, k32, k33 = fez["k31-map"], fez["k32-isolation"], fez["k33-payoff"]

prior = archive.isolation_analysis(k32, k31["pairs"], k31["archived"]["analysis"]["kA"])
k_prior, L_prior = prior["kD_all27"], prior["L_D_all27"]
x = [r["x"] for r in k33["published_at_submission"]]

by_map, by_x = pick_pairs(k_prior, 8), pick_pairs(x, 8, highest=False)
pairs = k33["pairs"]
print("chosen by the map:            ", [pairs[i] for i in by_map])
print("chosen by the published rates:", [pairs[i] for i in by_x])

payoff = archive.payoff_from_record(k33, k_prior, L_prior, archive.workload_ideal())
W = payoff["W"]
err_map = 1 - sum(W[i] for i in by_map) / 8
err_x = 1 - sum(W[i] for i in by_x) / 8
g = payoff["gains"]["k_prior"]
print(f"\nmean error on the workload (1 - W): map's pick {err_map:.5f}, published pick {err_x:.5f}")
print(
    f"the map's pick had {100 * (1 - err_map / err_x):.1f}% less error; G = {g['G']:+.4f}, "
    f"90% interval [{g['ci90'][0]:+.4f}, {g['ci90'][1]:+.4f}]"
)
print(f"verdict: {payoff['verdict']['verdict']}")

# Amendment A15: `manacitra pick` now ranks the kept share by its distance from the ideal, |1 - k|, after the dead-pair
# filter. The pick above is Kickoff 33's, as run (highest k); this is the same prior map under the new rule.
from manacitra.circuits import CIRCUITS  # noqa: E402
from manacitra.layout import pick_by_kept_share  # noqa: E402

level_prior = [v * CIRCUITS["A"].ideal_no for v in L_prior]  # each pair's mean P(A no) in Kickoff 32's dense condition
by_distance = pick_by_kept_share(k_prior, 8, level_prior)
print("\nunder |1 - k| (pick's default since Amendment A15):", [pairs[i] for i in by_distance])
if set(by_distance) == set(by_map):
    print("the same eight pairs as Kickoff 33's pick")
else:
    print("pairs only in Kickoff 33's pick:", [pairs[i] for i in by_map if i not in by_distance])
    print("pairs only under |1 - k|:      ", [pairs[i] for i in by_distance if i not in by_map])
