# Independent confirmation results

The method, comparator, thresholds, task-selection procedure, operators, model
revisions, statistics, and ten pass gates were frozen before the independent
roster was selected and before any confirmation outcome was observed.

## Dataset flow

| Stage | Count | Audit condition |
|---|---:|---|
| Zero-overlap native tasks | 60 | 30 ALFWorld, 30 ScienceWorld |
| Successful healthy references | 60/60 | no failed or replaced reference |
| Outcome-blind mutation specifications | 240 | four operators per task |
| Technically valid native replays | 240/240 | exact initial-state match |
| Behaviorally killed revisions | 202 | all retained |
| Native-surviving revisions | 38 | retained as controls |
| Healthy controls | 60 | retained as controls |
| Final candidate programs | 300 | 202 positive, 98 negative |
| Local-model judgments | 900 | three pinned families, no invalid output |

## Primary endpoint

| Validator | Balanced accuracy | Recall | Specificity |
|---|---:|---:|---:|
| Endpoint-only (primary comparator) | 77.48% | 54.95% | 100.00% |
| Ordered milestones | 77.48% | 54.95% | 100.00% |
| Nearest successful trace | 50.74% | 1.49% | 100.00% |
| Qwen3-4B judge | 49.50% | 99.01% | 0.00% |
| Phi-4-mini judge | 50.72% | 86.14% | 15.31% |
| Mistral-7B judge | 51.12% | 60.40% | 41.84% |
| **IWCC** | **88.12%** | **76.24%** | **100.00%** |

IWCC improves over the predeclared endpoint-only comparator by 10.64
percentage points. The environment/family-stratified task bootstrap 95% CI is
8.88--12.50 points. The two-sided paired task sign-permutation result is
`p=9.9999e-6` (100,000 fixed-seed draws). All ten frozen gates pass.

ALFWorld improves by 16.23 points and ScienceWorld by 3.41 points. Seven of
eight family strata improve and one ties. This supports an aggregate
cross-environment claim, not uniform strong transfer to every family.

## Secondary endpoints

- killed-revision recall by deletion, adjacent swap, truncation, and role
  substitution: 72.55%, 74.19%, 80.00%, and 76.67%;
- exact localization among detected kills: 63.64%; within one action: 94.16%;
- median CPU validation latency: 0.487 ms; p95: 1.145 ms;
- compiled artifact: 77 successful witnesses, 9 family contracts, 71 clauses,
  including 18 witnessed navigation edges;
- recall Wilson 95% CI: 69.91--81.58%; zero-observed-false-rejection Wilson
  upper endpoint: 3.77%.

Machine-readable truth is in `final/summary.json` and
`final/secondary_metrics.json`. The post-hoc secondary analysis does not alter
the frozen primary result.
