# Incremental Witnessed Contract Compilation

This repository contains the implementation, frozen protocols, native execution
records, model-control outputs, analysis, and manuscript sources for:

> From Traces to Witnessed Contracts: Incremental Precondition-Effect
> Compilation for LLM Agent Skills

Authors: Liang Song (first and corresponding author) and Zhai Jiabao.

Repository: https://github.com/ls680/iwcc-agent-skill-contracts

## What IWCC does

Executable agent skills can retain a plausible final action while silently
breaking navigation, possession, transformation, ordering, or role
dependencies. Incremental Witnessed Contract Compilation (IWCC) compiles
successful native traces into deterministic, provenance-carrying structural
contracts. It then screens complete skill-program revisions before environment
execution and reports the violated clause and action position.

IWCC is a pre-execution defect screen. It does not plan, repair programs,
certify semantic success, or replace native testing.

## Frozen confirmation

The independent confirmation contains 60 zero-overlap ALFWorld and ScienceWorld
tasks and 300 candidate programs:

| Result | Value |
| --- | ---: |
| Behaviorally killed revisions | 202 |
| Healthy or behaviorally equivalent controls | 98 |
| IWCC balanced accuracy | 88.12% |
| Strongest predeclared comparator | 77.48% |
| Absolute gain | 10.64 points |
| Task-stratified 95% CI | 8.88 to 12.50 points |
| Paired task permutation p-value | 9.9999e-6 |
| IWCC false rejections among controls | 0 of 98 |
| Median validation latency | 0.487 ms on one CPU process |

All controlled edits, including native-surviving edits, remain in the released
records. Development and confirmation evidence are separated, and validators
cannot access the private outcome file before post-hoc analysis.

## Quick verification

The released-record verification is CPU-only:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -r environment/requirements-analysis.txt
pytest -q
python scripts/audit_information_boundary.py
python scripts/verify_release.py
bash artifacts/verify_bundle.sh
```

Expected output includes `9 passed` and a JSON object with `"status":
"passed"`, 300 candidates, IWCC balanced accuracy `0.8811881188`, and absolute
gain `0.1064356436`.

See [REPRODUCE.md](REPRODUCE.md) for PDF rebuilding and the full RTX 3090
native-confirmation workflow.

## Repository layout

- `src/iwcc/`: contract compiler, abstract state, and validator
- `scripts/`: frozen data preparation, validation, analysis, and integrity tools
- `configs/`: development, confirmation, and model revisions
- `data/`: released development and confirmation records
- `results/`: predictions, metrics, tables, and figures
- `research/`: method locks, protocol, evidence matrix, and audits
- `reproduction/`: clean-workspace scripts and pinned lightweight dependencies
- `paper/`: English, Chinese, and journal-specific manuscript sources
- `submission/automated_software_engineering/`: target-journal upload package
- `artifacts/`: checksummed reproducibility bundle

The files named `private_labels.jsonl` contain experimental outcome labels used
only by the post-hoc analyzer; they do not contain personal or confidential
data.

## Citation

Citation metadata are available in [CITATION.cff](CITATION.cff). The versioned
software, data, and reproducibility archive is available from Zenodo at
https://doi.org/10.5281/zenodo.22851666.

## License and third-party material

The original code and repository materials are released under the Apache
License 2.0. Third-party components remain under their upstream licenses. In
particular, the pinned ScienceWorld JAR and its Apache-2.0 license are identified
in [reproduction/THIRD_PARTY_NOTICE.md](reproduction/THIRD_PARTY_NOTICE.md).
ALFWorld game data and model weights are not redistributed.
