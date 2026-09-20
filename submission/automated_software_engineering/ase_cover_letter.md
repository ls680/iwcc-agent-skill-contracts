# Cover Letter

20 September 2026

Editors  
*Automated Software Engineering*

Re: Original Paper submission, "From Traces to Witnessed Contracts:
Incremental Precondition-Effect Compilation for LLM Agent Skills"

Dear Editors,

Please consider our manuscript for publication as an Original Paper in
*Automated Software Engineering*. The paper addresses a practical maintenance
problem created by executable LLM-agent skills: a plausible revision may retain
its final goal action while silently breaking navigation, possession, or
transformation dependencies.

We introduce Incremental Witnessed Contract Compilation (IWCC), a
pre-execution validator that compiles successful native traces into
deterministic, provenance-carrying contracts over objective roles, milestones,
precedence, navigation, and producer-consumer dataflow. Each learned clause
retains its successful witnesses, and each rejection identifies a violated
clause and action position.

The evaluation separates exposed development evidence from a frozen,
zero-overlap confirmation. Across 60 ALFWorld and ScienceWorld tasks and 300
candidate programs, IWCC reaches 88.12% balanced accuracy, compared with 77.48%
for the predeclared strongest comparator. The 10.64-point gain has a
task-stratified 95% confidence interval of 8.88-12.50 points and a paired task
permutation p-value of 1.0 x 10^-5. IWCC accepts all 98 healthy or behaviorally
equivalent controls and runs at 0.487 ms median latency on one CPU process.

The work fits the journal's scope by treating reusable agent skills as evolving
software artifacts and combining specification mining, software validation,
provenance, and release-time defect screening. The claim is deliberately
bounded: IWCC detects modeled structural defects but does not certify semantic
success or replace native execution.

Source code, data, frozen protocols, analysis scripts, and the reproducibility
bundle are publicly available at
https://github.com/ls680/iwcc-agent-skill-contracts under Apache-2.0 and
archived at https://doi.org/10.5281/zenodo.22851666.

The manuscript is original, has not been published, and is not under
consideration elsewhere. Both authors have reviewed and approved the submitted
version, author order, and contribution statement. The authors received no
funding for this research and have no relevant financial or non-financial
interests to disclose. Generative-AI assistance is disclosed in the manuscript.

Thank you for considering our work.

Sincerely,

Liang Song  
Corresponding author  
Business School, Xi'an International University  
Xi'an, Shaanxi 710077, China  
liangsong_1976@126.com  
ORCID: 0009-0002-6109-0639
