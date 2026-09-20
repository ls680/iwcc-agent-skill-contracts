# Automated Software Engineering submission metadata

## Manuscript

- Title: From Traces to Witnessed Contracts: Incremental Precondition-Effect Compilation for LLM Agent Skills
- Short title: Witnessed Contracts for LLM Agent Skills
- Journal: Automated Software Engineering
- Proposed article type: Original Paper
- Language: English
- Abstract length: 161 words
- Keywords: Agent skills; LLM agents; specification mining; precondition-effect contracts; regression validation; execution traces
- Figure preparation: Matplotlib; the supplied `Fig1.pdf` is vector artwork with embedded fonts

## Authors

1. Liang Song (first and corresponding author)
   - Affiliation: Business School, Xi'an International University, Xi'an, Shaanxi 710077, China
   - Email: liangsong_1976@126.com
   - ORCID: https://orcid.org/0009-0002-6109-0639
2. Zhai Jiabao
   - Affiliation: School of Management and Economics, North China University of Water Resources and Electric Power, Zhengzhou, Henan 450046, China
   - Email: zhaijiabao123@126.com
   - ORCID: None provided

## Correspondence

Liang Song, Business School, Xi'an International University, Xi'an, Shaanxi
710077, China. Email: liangsong_1976@126.com.

## Abstract

Reusable agent skills are increasingly stored as executable programs but rarely
carry machine-checkable accounts of what actions require and produce. Revisions
can thus preserve plausible final steps while breaking navigation, possession,
or transformation dependencies. We introduce Incremental Witnessed Contract
Compilation (IWCC), which compiles successful traces into deterministic,
provenance-carrying contracts over objective roles, milestones, precedence,
navigation, and producer-consumer dataflow. IWCC screens candidates before
environment execution and reports violated clauses and action positions. After
development on exposed evidence, we froze the method and selected a
zero-overlap confirmation of 60 ALFWorld and ScienceWorld tasks. Four
outcome-blind operators yielded 300 candidates: 202 killed revisions and 98
controls. IWCC achieved 88.12% balanced accuracy versus 77.48% for the strongest
comparator, a 10.64-point gain (task-stratified 95% CI 8.88-12.50 points; paired
permutation p = 1.0 x 10^-5). Recall was 76.24%, all controls were accepted, and
both environments improved. Median validation time was 0.487 ms on one CPU
process. Thus, trace-backed contracts provide an auditable, low-false-alarm
screen for executable skill revisions; they do not certify semantic success or
replace native testing.

## Declarations

- Funding: This research received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors.
- Competing interests: The authors have no relevant financial or non-financial interests to disclose.
- Author contributions: Liang Song: Conceptualization, methodology, software, validation, formal analysis, investigation, data curation, visualization, writing--original draft, writing--review and editing, and project administration. Zhai Jiabao: Methodology, validation, and writing--review and editing. Both authors read and approved the final manuscript.
- Acknowledgements: The authors have no acknowledgements to report.
- Ethics approval: Not applicable. The study evaluates software artifacts and public software benchmarks and involves no human participants, animals, clinical data, or personally identifiable information.
- Consent to participate: Not applicable.
- Consent for publication: Not applicable.
- Generative-AI assistance: OpenAI Codex assisted with research-design iteration, code development, reproducibility packaging, language editing, and manuscript formatting. The authors reviewed and verified the code and text, reran the released integrity checks, evaluated the claims against the results, and take full responsibility for the work.

## Repository information

- Public source repository URL: https://github.com/ls680/iwcc-agent-skill-contracts
- Repository host: GitHub
- Repository license: Apache-2.0
- Versioned archival DOI: https://doi.org/10.5281/zenodo.22851666
- Dataset citation for the reference list: Song, L., & Zhai, J. (2026). *From Traces to Witnessed Contracts: Incremental Precondition-Effect Compilation for LLM Agent Skills (Software and Reproducibility Artifacts)* (Version 0.1.0). Zenodo. https://doi.org/10.5281/zenodo.22851666

The existing local artifact is
`artifacts/iwcc_reproducibility_bundle.tar.gz`; its contents are covered by
`artifacts/release_manifest.sha256`. The GitHub URL is public and the versioned
archive is registered under DOI `10.5281/zenodo.22851666`.
