# Literature grounding and gap

The design is grounded in the local Agent Skill lifecycle corpus rather than a
generic program-analysis analogy.

| Local-corpus work | What it already establishes | Gap retained for this paper |
|---|---|---|
| Lifting Traces to Logic / NSI | Traces can be lifted into logic-grounded programs with control flow and variable binding. | It does not isolate incremental, auditable precondition/effect contract maintenance as the evaluated artifact. |
| SKILL-DISCO | Successful traces can be compiled into reusable and verifiable PFSM subgraphs. | A program revision still needs a pre-execution certificate explaining which dependency or terminal effect it violates. |
| Skill-Pro | Skills benefit from explicit activation, execution, and termination conditions plus verification. | The conditions are part of a learning framework; the evidence provenance and order-stable incremental compiler remain separate questions. |
| SkillOps | Typed Skill Contracts make prerequisites, outcomes, actions, validation, and failure explicit. | The contract is a representation and maintenance interface; automatically compiling clauses from native traces and testing their mutation sensitivity is not its central experiment. |
| GraSP | Precondition-effect edges support graph execution, node verification, and local repair. | This paper stops before orchestration or repair and asks whether the contract itself can detect defective executable revisions without running them. |
| SkillFuzz | Extracted contracts can prioritize risky skill compositions without executing every combination. | Its unit is cross-skill implicit intent; the present unit is an intra-skill executable program revision with trace-backed clauses. |

The closest internal attempts are also important negative evidence. Revisions
13--15 of paper 01 found that holistic and factorized LLM action guards did not
produce complete-task gains. Revisions 16--18 compiled a ScienceWorld executor,
but the frozen implementation reached only 12/30 tasks. The present work must
not rename those attempts. It changes both the artifact and the endpoint:
IWCC validates complete candidate programs before execution; it does not act as
an online policy and does not claim to improve an LLM executor.

The proposed contribution is an incremental witnessed contract compiler. A
native command adapter emits typed fluents. Each successful trace supplies
positive witnesses for goal-role bindings, required milestones, producer-to-
consumer dependencies, and terminal effects. Clauses retain their supporting
trace hashes, and the merged contract is required to be independent of trace
arrival order. Candidate revisions are checked using only the task objective,
candidate program, initial public observation, and the previously compiled
contract. Native replay is used only as the held-out behavioral oracle.

