# Development protocol

Frozen for development on 2026-09-06. Independent confirmation remains sealed.

## Research question

Can successful native execution traces be incrementally compiled into
machine-checkable precondition/effect contracts that reject behaviorally broken
Skill revisions before execution, while preserving healthy and behaviorally
equivalent programs?

## Method boundary

Incremental Witnessed Contract Compilation (IWCC) receives successful traces
for a named Skill family. A small environment adapter parses native commands
into typed events. The compiler retains:

1. objective roles and the action arguments that bind them;
2. milestones supported by successful traces;
3. precedence clauses between supported milestones;
4. producer-consumer dataflow such as navigation before source access,
   acquisition before transformation/placement, and focus before transfer;
5. terminal effects required by the public task objective;
6. trace identifiers and hashes witnessing every emitted clause.

The incremental merge must be deterministic and independent of trace arrival
order. Rare successful alternatives are represented as witnessed branches and
must not be converted into failures merely because a majority path differs.
At validation time the method cannot read the candidate's native outcome,
mutation operator/index, healthy reference program, or gold continuation.

## Development evidence

Only previously exposed paper-04 development and confirmation traces and native
mutation outcomes may be used to implement adapters, set support thresholds,
select baselines, and debug metrics. These records cannot support the final
confirmatory claim.

Development examples contain healthy programs, killed mutations, and mutations
that remain successful. Both kinds of mutations must be retained. Healthy and
surviving revisions measure false rejection; killed revisions measure defect
detection.

## Comparators

The initial comparator set is:

1. endpoint-only contract: checks required terminal role/effect but not order or
   intermediate dataflow;
2. ordered milestones: checks learned milestone presence and order but not
   producer-consumer witnesses;
3. nearest successful trace: normalized sequence edit distance calibrated on
   development controls;
4. three frozen local instruction-model judges given the same objective and
   candidate program, with no native outcome or healthy reference.

The strongest non-oracle development comparator is designated as the primary
confirmation comparator before confirmation selection.

## Metrics and development gate

The unit is a candidate program, not a model sample. The primary endpoint is
balanced accuracy for separating native-killed revisions from healthy or
native-surviving programs. Secondary endpoints are killed-revision recall,
healthy/surviving specificity, exact or one-step violation localization,
contract size, compilation/update time, and order-invariance.

Development may advance only if all conditions hold:

- at least 80 native-killed revisions and 50 healthy/surviving controls across
  both environments;
- balanced accuracy at least 0.80;
- at least 10 percentage points over the strongest non-oracle comparator;
- healthy/surviving false rejection at most 5%;
- killed-revision recall at least 75%;
- positive improvement in both ALFWorld and ScienceWorld;
- all emitted clauses have at least one trace witness and 100 random trace
  insertion orders produce the same canonical contract.

Up to three mechanism-level development revisions are allowed. All failed
versions remain archived. Failure after three revisions moves the queue to
matrix item 06 without opening confirmation.

## Planned independent confirmation

After the method and analyzer are frozen, select at least 60 content-blind,
zero-overlap tasks from official ALFWorld validation and ScienceWorld test
splits. Collect successful healthy trajectories, generate mutation
specifications without reading outcomes, and retain every native replay. The
operator set must include deletion, adjacent order swap, suffix truncation, and
one argument/role substitution operator not used to tune the first compiler.

The confirmatory primary analysis is paired at task level. It uses a two-sided
100,000-draw sign-permutation test and an environment/family-stratified task
bootstrap with 10,000 draws, both under the frozen analysis seed.
Confirmation requires balanced accuracy at least 0.80, an absolute improvement
of at least 10 points over the frozen primary comparator, p <= 0.01, a positive
95% interval lower bound, false rejection at most 5%, recall at least 75%, and
positive effects in both environments. A failed gate is retained and the paper
is not entered in the completion index.

## Claim boundary

Controlled mutations are not production defects. Passing a structural
contract does not prove semantic task success, and rejecting a program does not
repair it. The intended claim is narrower: trace-backed contracts can provide
an auditable and low-false-alarm pre-execution screen for a specified class of
executable Skill revisions.

## Frozen confirmation design

The content-blind roster has 60 planned tasks: 5, 7, 6, 6, and 6 tasks from
the five reliable ALFWorld families respectively, plus ten from each of three
ScienceWorld families. This unequal allocation is fixed solely because only
five untouched `look_at_obj_in_light` tasks remain after prior-exposure
exclusion; it was chosen before any new task content or outcome was accessed.
The roster generator excludes every task appearing in Paper 01 revisions
22--24 or the Paper 03--04 confirmations before it reads task content or
outcomes. The development-frozen endpoint-only validator is the primary
comparator. Ordered milestones, a nearest-successful-trace detector fixed at
distance 0.6, and three revision-pinned local model judges are strong controls.
All healthy programs and naturally surviving mutations are negative controls;
no outcome is discarded for being inconvenient.
