# Reproducing IWCC

The release supports two levels of reproduction. The first is self-contained,
CPU-only, and verifies the exact published records. The second repeats all
native simulator executions and model judgments on one RTX 3090.

## 1. Exact released-record verification

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -r environment/requirements-analysis.txt
pytest -q
python scripts/audit_information_boundary.py
python scripts/verify_release.py
```

`verify_release.py` is read-only. It checks every method-lock hash; public,
private, deterministic, and model record alignment; all primary metrics; the
10,000-draw stratified task bootstrap; the 100,000-draw paired task
permutation test; all ten frozen gates; the information boundary; the pinned
simulator JAR; and both PDF signatures. Expected final status is `passed`, with
300 candidates, 202 killed revisions, 98 controls, IWCC BA 0.881188, gain
0.106436, CI [0.088828, 0.125000], and p=9.9999e-6.

The original `analyze_confirmation.py` deliberately refuses to overwrite an
existing confirmation summary. This is an analysis-once safeguard, not a
reproduction obstacle; the read-only verifier recomputes the same estimands.

## 2. Rebuild tables and bilingual PDFs

Install the TeX packages listed in `environment/RUN_ENVIRONMENT.md`, then run:

```bash
bash paper/build.sh
```

Outputs are `paper/en/main.pdf` and `paper/zh/main.pdf`. The build fails on
unresolved references, undefined controls, or overfull boxes.

## 3. Full native confirmation on an RTX 3090

Install PyTorch 2.8.0 for CUDA 12.8, then the pinned native requirements:

```bash
python -m pip install -r environment/requirements-native.txt
python -m pip install -e .
```

Place the Hugging Face cache and Python environment on the data disk. Set
`ALFWORLD_DATA` to the ALFWorld game-data root. The frozen roster contains the
relative game-file identifiers and hashes.

The historical experiment intentionally references sibling Paper 01, 03, and
04 paths so its method-lock hashes remain unchanged. A complete snapshot of
the exact lightweight dependencies and pinned 7.8 MB ScienceWorld JAR is
included in `reproduction/workspace_dependencies`. Prepare a clean sibling
layout outside the repository:

```bash
bash reproduction/prepare_workspace.sh /path/to/clean/iwcc-workspace
cd /path/to/clean/iwcc-workspace/05_witnessed_contracts
export ALFWORLD_DATA=/data/alfworld/json_2.1.1
export HF_HOME=/data/huggingface
bash reproduction/run_native_confirmation.sh
```

The native pipeline freezes the same zero-overlap roster, collects 60 healthy
oracles, generates four mutations per task without outcomes, executes all 240
mutations from matched initial states, builds public/private views, runs the
four deterministic validators and three pinned model judges, audits the
information boundary, then opens labels once for analysis. Scripts are
checkpointed: completed native episodes and model responses are retained, so
an interrupted run can resume.

Native simulator outcomes can vary if external dependencies, Java, game data,
or hardware differ. Such a rerun is an independent replication and should be
reported separately from exact verification of the released records.
