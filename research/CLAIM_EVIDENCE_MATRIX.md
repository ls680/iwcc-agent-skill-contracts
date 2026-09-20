# Claim-evidence matrix

| Claim | Evidence | Scope and restraint |
|---|---|---|
| IWCC improves pre-execution discrimination over the frozen primary comparator. | `results/confirmation/final/summary.json`: BA 0.881188 vs 0.774752; gain 0.106436; stratified task CI [0.088828, 0.125000]; paired task p=9.9999e-6. | Applies to the frozen 60-task, eight-family ALFWorld/ScienceWorld confirmation and four controlled operators. |
| The gain is not produced by rejecting every program. | 154 TP, 48 FN, 98 TN, 0 FP; specificity 1.0 and false-rejection rate 0. | Zero observed errors does not prove zero population error; Wilson upper endpoint is 3.77%. |
| Intermediate state/dataflow adds information beyond endpoint presence. | Endpoint recall on killed adjacent swaps is 0%; IWCC recall is 74.19%. Overall endpoint BA is 77.48%, IWCC BA is 88.12%. | Does not establish completeness for arbitrary semantic defects. |
| Confirmation is separate from method development. | `research/METHOD_LOCK_V2.json`, `data/confirmation/roster.json`, and run specs record timestamps, hashes, zero overlap, and `confirmation_outcomes_seen: false`. | V1 development failure and infeasible first roster lock are disclosed, not erased. |
| Validators had no access to outcomes or hidden task locators. | `research/INFORMATION_BOUNDARY_AUDIT.json`; public candidates have six allowed fields; all run specs record private labels unopened. | The analyzer opens labels only after all prediction files are complete. |
| Learned clauses are deterministic and auditable. | `results/development/v2/summary.json` records 100 order permutations; `contract.json` carries trace witness hashes and canonical SHA-256. | Witnessed properties are dynamic likely invariants, not universal proofs. |
| Results transfer directionally across both environments. | ALFWorld gain 16.23 points; ScienceWorld gain 3.41 points; seven family strata positive, one tied, none negative. | ScienceWorld BA is only 78.41%; the paper does not claim uniformly strong domain transfer. |
| Operational validation is inexpensive. | `secondary_metrics.json`: 30,000 calls, 0.487 ms median, 1.145 ms p95, about 1,715 programs/s on one CPU process. | Model-judge GPU cost is a comparator cost; native testing remains required for unmodeled semantics. |
| The released result can be checked exactly. | `scripts/verify_release.py` recomputes metrics, bootstrap, permutation, hashes, gates, and audits without rewriting results; `REPRODUCE.md` gives commands. | Full native replay additionally requires ALFWorld data, Java, and pinned external dependencies. |
