# Workflow

Use the route selected by [Change Classifier](change-classifier.md) for source-changing `debug` and `repair`; that reference is the sole authority for thresholds, route composition, and upgrades. Standalone `diagnose` uses stages 1-2 and standalone `review` uses stage 7. At `repair` entry, validate and normalize the supplied diagnosis and repair selection before the selected route's first writable phase. Return to stages 1-2 only when the diagnosis is stale or incomplete, or later evidence invalidates it. A standalone `review` remains project-source read-only and never transitions into diagnosis, planning, or repair without a new user-authorized scope. Repository-specific instructions override storage locations, commands, and commit policy.

The seven stages are: 1 Investigation, 2 Diagnosis, 3 Planning, 4 Implementation, 5 Integration, 6 Verification, and 7 Independent review. Stage 5 is topology-dependent: `SINGLE` records `INTEGRATION_REQUIRED: NO`; `POOLED` records `YES` and runs integration after every implementer stops.

Stages 2 and 3 always decide different questions—stage 2 decides what is wrong, stage 3 decides how the approved repair is executed—but they do not always run in different Agents. A minimal repair keeps planning inline in the same diagnostician; a structural or multi-task repair moves it to a dedicated planner with its own context.

## Change-classifier routing

After run control is resolved, apply [the classifier contract](change-classifier.md) before the first route phase and persist `classification.md`. Then execute exactly the selected route; do not maintain a second route table here. Classification is bookkeeping, not an Agent, stage, authority grant, or replacement for repair selection and safety gates. Reuse compatible evidence after an upgrade instead of repeating a phase solely to change its label.

## Early-exit rules

The nominal stage list is an upper bound. After every phase terminal result, apply the first matching rule before starting or dispatching the next phase:

| Condition | `EARLY_EXIT_REASON` | Exit after | Required evidence |
|---|---|---|---|
| Investigation finds no credible defect or actionable incident issue | `NO_ISSUE` | Investigation | Complete or bounded discovery, zero issues, and disproved candidates |
| In `debug` or `repair`, diagnosis leaves no approved actionable repair | `NO_ACTIONABLE_REPAIR` | Diagnosis | Per-issue classifications and reasons, including deferred items |
| In `debug` or `repair`, planning produces no executable task for the approved repair set | `NO_ACTIONABLE_REPAIR` | Planning | The frozen repair set, the blocking reason, and the rejected decompositions |
| In `debug` or `repair`, the user selects no repair | `NO_REPAIR_SELECTED` | Repair selection | Explicit selection and `SELECTED_ISSUES: NONE` |
| An approved repair is already present and focused verification passes without a source change | `CHANGE_ALREADY_PRESENT` | Verification | `IMPLEMENTATION_STATUS: NO_CHANGE` plus focused verification of the original invariant |
| A standalone review has no changed artifact in its explicitly resolved scope | `EMPTY_REVIEW_SCOPE` | Review scope check | The resolved comparison target and evidence that its diff is empty |

`NEEDS_DECISION` and `BLOCKED` are not early-success conditions. An absent implementation diff is also not success while the approved issue remains: record a partial or blocked outcome. A valid early exit produces the artifacts and markers for phases actually run plus one `处理总结`; skipped phases remain unmarked. Full and early completions may clean the current run directory, while partial, failed, blocked, stopped, cancelled, and paused exits retain it.

## Workspace and artifact location

Before creating any workflow artifact, resolve the repository root and automatically discover whether the project already defines a shared intermediate-artifact root. Inspect only cheap, relevant evidence in this precedence order:

1. repository instructions such as `AGENTS.md` and an explicitly documented artifact-path policy;
2. project configuration or quality scripts that route several rebuildable outputs—tests, lint, coverage, build, or diagnostics—under one common root;
3. an existing repository-root `.artifacts/` or `artifacts/` directory that is clearly designated for intermediate outputs and is ignored by version control.

An explicit repository instruction wins. Do not infer a shared root from one tool's private cache, a source/output directory, or runtime locations such as `data/`, `logs/`, `backups/`, database storage, or deployment staging. Resolve relative paths from the repository root, never from an arbitrary process working directory. In a Git workspace, verify the selected in-repository root is ignored or explicitly approved before writing. If equally authoritative candidates conflict, or no safe project root exists, use a unique system temporary directory and disclose that fallback instead of creating a new repository convention.

Place Multi-Agent Incident Resolution records in a collision-safe run directory under the selected root, normally `<artifact-root>/multi-agent-incident-resolution/<YYYY-MM-DD_HH-mm-ss>/`. Derive the base name from the host's configured local wall-clock timezone, not UTC, with `date '+%Y-%m-%d_%H-%M-%S'`, and create the directory atomically. If the base name already exists, append the first available zero-padded decimal discriminator (`-01`, `-02`, ...); never wait for wall-clock time to advance, overwrite, or reuse another run's directory. Reuse the resolved run directory across all phases and delegated Agents. Record both the resolved root and run directory in the first artifact and every Agent handoff.

The current run directory is disposable only under [Run artifact cleanup](#run-artifact-cleanup). Until cleanup begins, treat it as required workflow evidence.

Before delegating, record the incident input and workspace root. Every phase must read the same incident input and applicable repository instructions. Later phases read prior artifact files rather than receiving a rewritten narrative.

Apply the selected run-control mode from [confirmation.md](confirmation.md). In **单步确认** mode, stop before stages 1-7 and before every Agent switch or parallel Agent batch; present the required checkpoint and wait. A phase terminal marker does not authorize the next phase. Planning has its own stage checkpoint before the implementation checkpoint even when `INLINE` reuses the diagnostician; `DEDICATED` planning additionally introduces a new Agent route. Confirm one implementer wave as one packaged batch only when `execution_mode` permits concurrency and every task in that wave passes the parallel-safety criteria; confirm integration as its own checkpoint.

## Subagent state, liveness and result visibility

Before dispatching or monitoring a subagent, follow [subagent-state.md](subagent-state.md) as the sole authority for task paths, checkpoints, observation, intervention, terminal preservation, and worker reclamation. Create the dispatch-ledger record required by [artifacts.md](artifacts.md) before dispatch. Do not change phase or exit until its result-consumption, runtime-termination, ledger, and visible-relay gates are complete; apply [the routing-disclosure contract](confirmation.md#subagent-routing-disclosure) to that relay.

Throughout this workflow, `terminal-complete` means that a dispatch satisfies both the handoff and verified runtime-termination gates in [Terminal handling](subagent-state.md#terminal-handling). Task evidence alone is insufficient.

## Phase context reset

The coordinator owns the active context at every stage boundary. It must rebuild that working set at the two mandatory reset points below instead of carrying the conversation or prior Agent reasoning forward:

1. after planning is terminal-complete and before implementation is authorized or dispatched;
2. after a repair-attributable verification failure and before the next diagnosis dispatch.

At either point, write or atomically replace `<RUN_ARTIFACT_DIR>/active-context.md` using [the active-context contract](artifacts.md#active-context-and-repair-rounds). A reset is complete only when the capsule identifies the current source/worktree state, repair round, authorized scope, constraints, task state, next gate, and a small allowlist of authoritative artifact paths or precise sections. The coordinator then treats only that capsule, its allowlisted references, current repository instructions, and new user input as active working context. Conversation history, exploration narratives, rejected hypotheses, full command output, previous implementation reasoning, unrelated task results, and superseded plans remain on disk for audit but are not carried or reread by default.

Use a runtime context-reset or compaction primitive when one is actually available. Its absence does not permit an unbounded handoff: perform the logical reset above, stop relying on unlisted conversational memory, and dispatch the next Agent with a fresh bounded context. Never claim that physical context was erased when the runtime cannot prove it. Reopen excluded history only to resolve a named contradiction or missing fact; first add that exact source and reason to `active-context.md`, then remove it from the allowlist at the next reset.

`active-context.md` is an index, not another narrative summary. Point to canonical artifacts and exact failure records instead of copying them. If the capsule is stale, internally inconsistent, or too broad to identify the next bounded action, record `CONTEXT_STATUS: BLOCKED` and do not cross the phase gate.

## 1. Investigation

Goal: establish reproducible facts without editing source.

Use one primary investigator. Add parallel read-only investigators only when the issue has genuinely independent surfaces, such as logs, code paths, and runtime/environment evidence.

Produce `evidence.md` with:

- expected and observed behavior;
- trigger and reproduction status;
- timestamped evidence and exact commands;
- earliest causally relevant failure;
- relevant code path and invariant candidates;
- facts separated from hypotheses;
- unexplained gaps;
- `EVIDENCE_STATUS: COMPLETE` or `EVIDENCE_STATUS: BLOCKED`.

Do not recommend a patch merely because a log line looks suspicious.

Also maintain `issue-ledger.md` using [multi-issue.md](multi-issue.md). Continue targeted discovery after the first issue only while evidence stays within the incident boundary. Merge duplicate symptoms and record independent candidates instead of forcing all evidence into one root cause.

Before starting diagnosis, apply [Early-exit rules](#early-exit-rules). If no credible issue remains, finalize the investigation artifacts and exit; do not dispatch a diagnostician or proceed because `debug` nominally lists later stages.

## 2. Diagnosis

Use an independent diagnosis Agent, default `gpt-5.6-sol/medium`, for `normal` and `complex` routes. It must read the incident input and `evidence.md`, inspect relevant source as needed, and make no edits. Tiny has already passed the classifier's bounded-change gate and does not dispatch this role; if its implementer cannot stay within that gate, upgrade to Normal before continuing.

Diagnosis answers what is broken, why, and how far it reaches. Whether it also plans depends on `PLANNING_MODE`:

- `PLANNING_MODE: INLINE` — the default for a `MINIMAL` repair. The same diagnostician and context own stage 3 and produce `plan.md` plus a single-task `tasks.yaml`. It may continue in the same dispatch only when the repair set is already frozen and no run-control checkpoint intervenes; otherwise it hands off after diagnosis and is resumed for a new bounded planning dispatch after the gate. It designs no refactor, creates no waves, and stops at one task.
- `PLANNING_MODE: DEDICATED` — a separate planner Agent owns stage 3 with its own context. The diagnostician then stops at cause and impact: it does not decompose work, does not design the target structure, does not choose execution order, and must not produce `plan.md` or `tasks.yaml`.

The coordinator resolves and records the mode from the completed diagnosis before stage 3 starts, using [the planning-mode rule](#planning-mode). A diagnostician may recommend a mode, but it cannot cross a pending repair-selection or single-step gate on its own.

Produce `diagnosis.md` with:

- symptom, trigger, contributing factors, root cause, and downstream effect;
- causal chain and violated invariant;
- the invariant a repair must restore or enforce;
- impact scope: affected modules, files, symbols, contracts, data, callers, and tests, with the blast radius of each candidate repair direction;
- `REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED | UNDETERMINED`, and, for `STRUCTURAL`, why no focused patch can enforce the invariant;
- the smallest plausible correct patch, only as feasibility evidence for the repair direction and never as an implementation design;
- rejected alternatives and why;
- focused and regression acceptance tests;
- `CONFIDENCE: HIGH | MEDIUM | LOW | MIXED`;
- `REPAIR_APPROVED: YES | PARTIAL | NO`;
- `DIAGNOSIS_STATUS: COMPLETE | BLOCKED`.

For multiple issues, these top-level markers may use `REPAIR_TYPE: MIXED`, `CONFIDENCE: MIXED`, and `REPAIR_APPROVED: PARTIAL`; the issue ledger must retain the exact per-issue values that govern repair selection.

Diagnose and classify every issue in `issue-ledger.md`. A full diagnosis may be complete when some issues are explicitly `BLOCKED`, `DEFERRED`, `DUPLICATE`, or `NOT_A_DEFECT`, but each such status needs evidence and a reason.

In `debug` or `repair`, if diagnosis leaves no approved, actionable repair for this run, apply [Early-exit rules](#early-exit-rules) and exit after recording the diagnosis; do not dispatch a planner and do not continue into planning. A standalone `diagnose` completes at its normal scope boundary at the end of stage 2 and never produces `plan.md`, `tasks.yaml`, or source edits. A repair menu is unnecessary when there are no eligible repairs. If the user explicitly chooses not to repair, record the selection and exit without planning, implementation, or review.

Consider expert escalation when confidence is low, minimal versus structural is unresolved, the issue crosses multiple modules, it involves concurrency/state machines/complex data models, or the same repair direction has failed twice. Start from the diagnosis default, `gpt-5.6-sol` with `medium` effort. A stronger model, effort, or compute mode follows the authorization contract in [confirmation.md](confirmation.md), including in automatic mode. The expert returns `PROCEED` or `RETURN_TO_DIAGNOSIS`; it does not edit source. Do not plan or implement while it recommends returning to diagnosis.

## 3. Planning

Planning turns the frozen repair set into executable work for Normal and Complex routes. It runs after diagnosis and repair selection, and no Normal/Complex implementer is dispatched before `plan.md` and `tasks.yaml` exist. Tiny is the documented exception: the coordinator materializes its one-task `tasks.yaml` from the complete classifier envelope and does not create `plan.md`.

Enter planning only with `DIAGNOSIS_STATUS: COMPLETE`, `REPAIR_APPROVED: YES` for every selected issue, and a frozen, non-pending `SELECTED_ISSUES`.

When the initially selected repair first enters planning, set `REPAIR_ROUND: 1` and append its `OPENED` event to `repair-rounds.md`. A later round enters planning only after its fresh diagnosis has reassessed the current state.

### Planning mode

The coordinator chooses `PLANNING_MODE` before this stage starts and records it with the dispatch ledger:

| Mode | When | Who runs stage 3 | Route |
|---|---|---|---|
| `INLINE` | `NORMAL` with one selected issue or one shared repair direction, `MINIMAL`, and a single-module blast radius | the same diagnostician and retained context; a gate may require a new bounded dispatch | `gpt-5.6-sol/medium` |
| `DEDICATED` | `COMPLEX`, or any `STRUCTURAL`/`MIXED`, multi-issue, multi-module, migration, deletion, parallel, or explicitly refactor-planned repair | a separate planner Agent with its own context | `gpt-5.6-luna/max` |

Default to `INLINE` only for the Normal route. Complex always uses `DEDICATED`; the point of the split is context isolation for large changes, not ceremony for small ones.

In `INLINE` mode the diagnostician also writes `plan.md` and a one-task `tasks.yaml`, reusing its canonical Agent label. When repair selection or a single-step checkpoint interrupts the stage transition, it first completes the diagnosis handoff; after the gate, the coordinator resumes the same Agent/context with a new bounded planning dispatch, ledger record, and task-state path. If it discovers that the repair needs more than one task, dependency waves, or an integration step, it must stop planning, record `PLAN_STATUS: BLOCKED` with the evidence, and hand back to the coordinator, which switches the run to `DEDICATED` and dispatches a planner. It must not stretch an inline plan into a multi-task decomposition.

In `DEDICATED` mode the planner reads the incident input, `evidence.md`, `diagnosis.md`, `issue-ledger.md`, applicable repository instructions, and the current diff; it may inspect source read-only to find seams, callers, and dependency boundaries. It does not inherit the diagnostician's working memory.

The planner decides how the approved repair is executed, never what is wrong. It must not redesign the root cause, change `REPAIR_TYPE`, reclassify issues, or modify the frozen selection. When the diagnosis cannot support a safe decomposition, it stops, records `PLAN_STATUS: BLOCKED` with the evidence and the exact contradiction, and returns the run to stage 2; it must not silently invent a different repair direction.

Produce `plan.md` with:

- the requirement being satisfied, organized into the smallest set of complete repair closures tied to the selected issue IDs;
- the refactor or repair approach, and why it wins over the rejected alternatives;
- the task decomposition and why these boundaries, including what stays out of scope; when there is more than one task, record for every split why it is needed, why the work cannot remain merged, and what parallel benefit exists or why execution must remain serial;
- the task dependencies, execution order, and resulting waves;
- `execution_mode: sequential | parallel | mixed` and `execution_reason`, explaining why tasks can or cannot overlap and what measurable benefit any concurrency provides;
- the integration strategy: expected seams, shared contracts, call-site updates, and known conflict points;
- per-task and whole-run acceptance criteria, including the commands or assertions that prove them;
- risk, blast radius, rollback approach, and the verification strategy for stage 6;
- `PLAN_STATUS: COMPLETE | BLOCKED`.

Produce `tasks.yaml` using [the task-contract schema](artifacts.md#task-contract). It records `execution_mode`, `execution_reason`, every subtask's `task_dependencies` and wave, owner, exclusive file scope, and acceptance conditions, plus `integration_required` and `integration_scope`. A task is dispatchable only when its owner, scope, dependencies, wave, and acceptance conditions are explicit; `SINGLE` keeps the integration scope empty, while `POOLED` must declare the Integrator's write boundary.

In `INLINE` mode the dependency graph, waves, and execution strategy collapse to one line each: one task, one wave, one implementer, and `execution_mode: sequential`. Record them in that form instead of omitting them, so the task contract stays uniform across both modes.

### Task and pool shape

Derive the implementation shape in this order: independent repair closures, then tasks, then the minimum useful number of implementation Agents. A repair closure includes all related code, tests, documentation, wiring, and validation work needed to restore one invariant and prove it. Merge related changes by default, including changes across different files, modules, or functions; those locations are scope metadata, not task boundaries.

Split a repair closure into separate tasks only when every resulting task has all four of the following: an independent problem goal, independent acceptance criteria, an independent execution path, and an independent risk boundary. File-scope disjointness is required for concurrent writers but is neither a reason to split nor sufficient evidence that parallel execution is safe. If any condition is missing, keep the work in one task.

Size the resulting decomposition and implementation pool as follows:

- `MINIMAL` normally yields one repair closure, one task, and one implementation Agent.
- `STRUCTURAL` or `MIXED` may yield several tasks with explicit waves, but its type, size, or module count does not by itself justify splitting. Use `IMPLEMENTATION_MODE: POOLED` only when at least two valid repair-closure tasks remain after merging related work; `execution_mode` separately determines whether those implementers run sequentially, concurrently, or in mixed waves.
- Tasks that must touch the same file belong to one task or leave that shared seam for the later integrator, never to two implementers. The later `integration_scope` may include task-owned files because every implementer has stopped before integration.

### Execution mode

After task boundaries are stable, analyze dependencies and choose the execution mode before creating implementation Agents. Default to `sequential`; concurrency is an optimization that requires affirmative evidence, not the consequence of having several tasks or available runtime slots.

- `sequential`: one task per wave. Use it whenever tasks depend on one another, modify the same core module, share an architectural decision or unified refactor direction, introduce or consume an interface change, or otherwise require an earlier result to stabilize the next task.
- `parallel`: one or more concurrent waves, which may be batched to respect the Agent budget. Use it only when every pair of tasks in each wave is low-coupling, has non-conflicting write scope, shares no unresolved core design decision, can be validated independently, and can fail without blocking or invalidating the other tasks. All five conditions are mandatory. Unrelated dispatches do not create an implicit global dependency.
- `mixed`: ordered waves containing both forms—for example, a serial foundation or interface change, followed by a concurrent wave of independent consumers, then planned integration. Each concurrent wave must satisfy all parallel conditions, and each dependent wave waits for its declared predecessors to become `terminal-complete`. Dependencies and shared decisions remain in earlier single-task waves.

`execution_reason` names the decisive dependencies, coupling, shared decisions, interface boundaries, failure propagation, and expected parallel benefit. The planner must not delegate execution-mode judgment to implementers or the integrator, and a requested parallel run is still subject to these constraints.

Before setting `PLAN_STATUS: COMPLETE`, the planner performs and records an execution-readiness self-check: whether any tasks can still be merged, whether each task is a reasonably sized complete repair closure, whether the dependency graph and waves match the selected execution mode, whether every concurrent wave passes all five parallel conditions, and whether the implementation Agent count is the minimum useful count. Default to one implementation Agent and a maximum of three. A plan above three must record why the tasks cannot be merged, why that degree of parallelism is necessary, and the concrete parallel benefit; without all three, merge the candidate work until the pool is within budget.

Every task in `tasks.yaml` must carry an acceptance condition that stage 6 can execute or check, and the union of task scopes plus `integration_scope` must cover the approved repair while staying inside the frozen `SELECTED_ISSUES` and the authorized file boundary.

A request for a plan without code changes is not a separate run mode: run `debug` or `repair` to this stage, then stop or pause at the planning checkpoint. `plan.md` and `tasks.yaml` are retained as deliverables, and no implementer is dispatched.

In `debug` or `repair`, if planning produces no executable task, apply [Early-exit rules](#early-exit-rules) with `EARLY_EXIT_REASON: NO_ACTIONABLE_REPAIR` and `EARLY_EXIT_PHASE: PLANNING`.

Consider expert escalation when the planner cannot produce a safe decomposition, dependencies are circular or unresolvable, every candidate violates file-disjointness, or the same plan direction has been rejected twice. Escalation follows the same authorization contract in [confirmation.md](confirmation.md); the expert is read-only and returns `PROCEED` or `RETURN_TO_DIAGNOSIS`.

After `PLAN_STATUS: COMPLETE`, perform the mandatory planning-to-implementation context reset for Normal and Complex. Retain the final plan, `tasks.yaml`, frozen issue selection, approved invariants, repository and user constraints, current worktree snapshot, run state, route, and next implementation gate. Exclude planning exploration and all evidence not needed by a listed task. Tiny has no planning reset; its materialized task contract and `classification.md` are its bounded implementation context. In `STEP` mode, build the capsule before presenting the implementation checkpoint, then revalidate its revision and worktree summary after approval; any drift returns to planning instead of dispatching against stale context.

## 4. Implementation

Tiny is the sole exception to the normal preconditions: after a complete Tiny classification and the applicable repair authorization, the coordinator materializes a single bounded task in `tasks.yaml`, freezes its change scope, and may dispatch one Implementer without `DIAGNOSIS_STATUS: COMPLETE` or `PLAN_STATUS: COMPLETE`. This task must carry the exact `file_scope` and executable acceptance conditions from the structured envelope. Normal and Complex proceed only with `DIAGNOSIS_STATUS: COMPLETE`, `PLAN_STATUS: COMPLETE`, a valid per-issue approval, and an explicit repair-set choice under [multi-issue.md](multi-issue.md). Freeze `SELECTED_ISSUES` or the Tiny change scope before writing. Newly discovered issues return to triage and selection rather than silently expanding implementation.

Create and dispatch implementation Agents only as authorized by the validated `execution_mode`, one implementer per task in `tasks.yaml`. `sequential` dispatches one task at a time in wave order; `parallel` dispatches each eligible wave as one concurrent batch; `mixed` alternates single-task and concurrent waves exactly as planned. Start no dependent task before every `task_dependencies` entry is `terminal-complete`; this restriction does not serialize unrelated parallel work. Never let two implementers write the same file concurrently. `IMPLEMENTATION_MODE: SINGLE` dispatches exactly one implementer owning one complete repair closure; `POOLED` dispatches several, each with a stable identifier such as `实施 Agent A`. Do not pre-create later-wave Agents or expand the pool merely because more tasks, files, or runtime slots are available. If current state invalidates the planned mode or a parallel-safety condition, stop before the affected wave and return to planning; implementers and the integrator do not reschedule the run.

Keep each implementer's context small. Give it only:

- a short incident summary and the frozen issue IDs its task covers;
- its own `tasks.yaml` entry: task ID, exclusive file scope, `task_dependencies`, wave, and acceptance conditions;
- the relevant excerpts of `classification.md`, `evidence.md`, `diagnosis.md`, and `plan.md` for that task, or their paths when an excerpt would be lossy;
- repository instructions, the validated `active-context.md`, the current working-tree snapshot, the run directory, repair round, and attempt number;
- its assigned `tasks/<task-id>/state.md` path, terminal handoff states, and the obligation to end its turn immediately after handoff.

Do not pass the whole incident history, unrelated tasks, or unrelated artifacts merely for completeness; per-task context isolation is what keeps the pool cheap and reliable.

Every implementer must:

- write only inside its assigned file scope;
- preserve unrelated and pre-existing changes;
- implement the smallest change that satisfies its own acceptance conditions;
- keep public behavior stable unless the approved diagnosis requires a contract change, and report a required contract change rather than making it silently;
- add or adjust tests to prove behavior, never merely to make assertions pass;
- update required architecture/product documentation when its task owns that surface;
- track any temporary logging, probes, breakpoints, fixtures, generated data, or configuration it used, so verification can prove they were removed or intentionally retained;
- avoid opportunistic cleanup and unrelated formatting;
- follow repository-specific environment and commit rules;
- leave cross-task seams, interface mismatches, and out-of-scope defects recorded instead of fixing them.
- for Tiny, stop with a terminal `BLOCKED` handoff whose result records `UPGRADE_REQUESTED` when the actual scope, dependency, risk, or design no longer matches `classification.md`; do not widen the edit or continue a second design inside the Tiny task.

Each implementer produces `implementation/tasks/<TASK-ID>.md` with its task ID, covered issue IDs, attempt number, files changed, behavioral differences, deviations from the task contract, tests added, unresolved seams handed to integration, and `TASK_IMPLEMENTATION_STATUS: COMPLETE | NO_CHANGE | PARTIAL | BLOCKED | FAILED | CANCELLED`.

The coordinator aggregates the per-task records into `implementation.md` containing the selected issue IDs, `IMPLEMENTATION_MODE`, `EXECUTION_MODE`, `IMPLEMENTER_COUNT`, executed waves, outcome per task ID, per-issue or shared-direction attempt numbers, files changed, behavioral differences, deviations from diagnosis or plan, tests added, seams handed to integration, and `IMPLEMENTATION_STATUS: COMPLETE | NO_CHANGE | PARTIAL | BLOCKED`.

On the first failed direction for a task, issue, or shared root-cause group, return it with the findings before a second attempt: to planning when the decomposition, task boundary, or acceptance conditions are at fault, and to diagnosis when the repair direction itself is at fault. After the second failed direction, stop patching that unit and invoke expert escalation; do not start a third attempt. In a pool, an independent task may continue only when it does not depend on the stopped unit and doing so remains safe.

If the implementer finds that the approved repair may already be present, use `IMPLEMENTATION_STATUS: NO_CHANGE` and record why. Proceed to focused verification of the original invariant; only a passing result permits `EARLY_EXIT_REASON: CHANGE_ALREADY_PRESENT`. If the check fails or cannot distinguish the diagnosis from a pre-existing or environmental failure, end partial or blocked rather than treating the absent diff as success. Integration and independent review are unnecessary when the resolved comparison confirms that this run made no source change.

## 5. Integration

Integration is a conditional assembly phase, not a second implementation. Run it only for `POOLED` after every implementation worker is `terminal-complete`, even if one or more tasks ended `NO_CHANGE`. `SINGLE` records `INTEGRATION_REQUIRED: NO` and `INTEGRATION_STATUS: SKIPPED`, then goes to stage 6. The planned task topology determines this gate; do not infer it afterward from how many files or workers happened to write.

Assign exactly one Integrator after every implementation worker has stopped, and let it be the only source writer while it runs. Give it the incident input, `classification.md`, `plan.md`, `tasks.yaml`, every `implementation/tasks/<TASK-ID>.md`, the frozen `SELECTED_ISSUES`, the current diff, and the integration strategy from `plan.md`. Its write authority is limited to `run.integration_scope`; an additional required path returns to planning instead of being edited opportunistically.

The integrator must:

- assemble the already-shared working-tree changes into one coherent result;
- resolve conflicts and duplicated or divergent edits introduced by parallel implementers;
- repair interface, signature, type, contract, and naming mismatches across task boundaries;
- complete missing wiring: call sites, registration, exports, routes, migrations, configuration, and documentation cross-references;
- prove the whole assembles by running the repository-prescribed build, type, or smoke checks;
- record every deviation from `tasks.yaml` and every seam it resolved.

The integrator must not redesign the approved repair, choose or revise `execution_mode`, reorder implementation tasks, change acceptance criteria, implement unselected or deferred issues, or silently expand scope. When assembly reveals a wrong decomposition, schedule, or missing task boundary, it stops and returns the run to planning; when it reveals a wrong repair direction, it returns to diagnosis. Record the evidence either way.

Produce `integration.md` with the tasks merged, conflicts and interface mismatches resolved, missing connections completed, checks run and their results, deviations from the task contract, unresolved items returned to planning, and `INTEGRATION_STATUS: SKIPPED | COMPLETE | PARTIAL | BLOCKED`.

## 6. Verification

Verification is a separate judgment from implementation and integration. For Tiny, after the Implementer is `terminal-complete`, the coordinator performs the bounded quick check itself; no Verifier Agent is dispatched. Normal and Complex use a delegated Verifier only after every writer is `terminal-complete`. Each route judges only whether the result satisfies its requirement and acceptance criteria.

Tiny quick verification checks the task acceptance conditions, the focused behavior, the final diff, and disposable diagnostic residue. It does not expand into broad regression or recurrence discovery. A passing quick check completes the Tiny route; an in-scope failure that cannot be resolved inside the original one-file contract closes an immutable failure snapshot and upgrades to Normal through the repair-round rules below. Environmental or pre-existing failures remain blocked instead of triggering an automatic retry.

The verifier must not merge branches, resolve conflicts, repair defects, or edit source; it verifies and reports. Classify each finding by the phase that owns the correction:

- a defect inside one task's file scope is implementation-owned;
- a seam, interface, conflict, or missing-connection defect across tasks is integration-owned;
- an acceptance-condition, task-boundary, or wave-ordering defect is planning-owned;
- a requirement or repair-direction defect is diagnosis-owned.

This classification does not authorize a direct return to a writer. A repair-attributable failure follows the fresh diagnosis and planning loop below; the owner tells that loop which contract or repair surface must change.

Validate progressively:

1. reproduce the original failure or its focused regression test;
2. run the focused test;
3. run relevant integration tests;
4. run proportionate broader regression, lint, type, or build checks;
5. perform one bounded recurrence scan for the same violated invariant or defect pattern within the incident's affected surface;
6. inspect the final diff and workspace for unintended changes and diagnostic residue.

The recurrence scan is discovery, not blanket repair authority. Record its exact scope and search method. Set `RECURRENCE_SCAN_STATUS: CLEAR` with `RECURRENCE_TRIAGE_STATUS: NOT_NEEDED` when no credible candidate is found. Otherwise set the scan to `FINDINGS` and triage to `PENDING`, add candidates to `issue-ledger.md`, and do not modify them unless the user selects them through the repair menu. Set triage to `COMPLETE` only after every finding is classified, selected, or explicitly deferred. Merge duplicates and downstream symptoms instead of inflating the issue count. Do not expand the scan into a repository-wide cleanup.

Diagnostic residue includes temporary logs, probes, breakpoints, debug-only branches, fixtures, generated data, environment overrides, and configuration changes. Remove disposable residue before completion. If any item is intentionally retained, justify it as part of the approved repair and test it accordingly.

Do not treat a passing unrelated test as proof. Classify failures as repair regression, implementation error, diagnosis error, environment problem, or pre-existing failure.

Produce `verification.md` with per-issue commands and results, per-task acceptance-condition outcomes when the run was pooled, shared-root-cause symptom coverage, combined regression results, original reproduction outcome, recurrence-scan scope and findings, recurrence-triage state, diagnostic-residue check, unexplained failures, coverage limits, and `VERIFICATION_STATUS: PASS | PARTIAL | FAIL | BLOCKED`. When verification does not pass, also write an immutable, concise `verification/round-<NNN>.md` failure snapshot and make `verification.md` reference it; later rounds never overwrite that snapshot.

### Verification-failure repair rounds

`REPAIR_ROUND` starts at `1` when the first selected repair enters planning, or when a Tiny task is frozen for its first implementation. A verification result of `FAIL`, or a `PARTIAL` result that identifies an in-scope repair defect, closes the current round as `VERIFICATION_FAILED`. Before any source writer is dispatched again, the coordinator must:

1. finish the coordinator quick-validation record or reclaim the delegated Verifier, then freeze the current `verification/round-<NNN>.md`, including the exact failing command/assertion, concise error, failure classification, affected issue/task IDs or `CHANGE_ID`, current revision and worktree state;
2. append the current round's `VERIFICATION_FAILED` event and the next round's `OPENED` event to `repair-rounds.md`, increment `REPAIR_ROUND`, and atomically rebuild `active-context.md` for `TARGET_PHASE: DIAGNOSIS` with only the current state and the immutable verification-failure references;
3. start a fresh bounded diagnosis dispatch from that capsule, then run stage 3 again to refresh the plan and `tasks.yaml` before implementation.

The new diagnosis must reassess the failure against the current code and may confirm the prior direction, but it must not inherit or assume the previous implementation reasoning. The refreshed plan may reuse stable task IDs only when their ownership and scope remain valid; it records which tasks are superseded, retained, or retried. Route classification still determines what the new diagnosis and plan must correct—task implementation, cross-task integration, decomposition/acceptance, or the repair direction—but verification failure never jumps directly back to a writer.

`REPAIR_ROUND` is an orchestration cycle, not an attempt allowance. Incrementing it does not reset the per-issue, shared-direction, or task `attempt`; the two-attempt limit remains cumulative. A `BLOCKED` verification or a failure classified as purely environmental/pre-existing does not automatically open a source-repair round: preserve the evidence and stop or request the missing condition unless an in-scope repair defect is established. Newly discovered issues still require triage and repair selection before inclusion.

## 7. Independent review

Tiny and Normal intentionally end after their applicable verification: they do not dispatch an independent reviewer and must not represent that omission as a pass. Record `INDEPENDENT_REVIEW: SKIPPED_BY_ROUTE`. Complex and standalone `review` use this stage. For Complex, use a read-only reviewer that neither implemented nor integrated the patch whenever the client and current Agent ownership make that possible. Prefer a fresh Agent with isolated context; a coordinator that did not write the patch also qualifies. The reviewer reads the incident input, requirement, relevant artifacts, applicable repository instructions, final diff, changed source, and verification results. It must not edit, commit, stash, or reset anything. Record `REVIEW_INDEPENDENCE: INDEPENDENT`.

If a route that requires independent review has no independent reviewer available, a coordinator that implemented or integrated the patch may perform a separate read-only fallback pass only when all of these are true: one selected issue, `MINIMAL`, `SINGLE` implementation mode, first implementation attempt, no integration work, low blast radius, and no security, public-contract, persistence, migration, concurrency, lifecycle, or state-machine impact. This fallback does not reintroduce review into Tiny or Normal, whose omission is explicit in the route contract. Stop editing before the fallback, re-read the stated requirements and final diff, run the same review rubric, record `REVIEW_INDEPENDENCE: LIMITED`, and disclose the limitation. For any other required-review repair, record `REVIEW_INDEPENDENCE: UNAVAILABLE` and `DECISION: BLOCKED`; do not weaken the classification merely to complete the run.

Judge the requirement, the final code, and the verification results together. Review adversarially for:

- whether the change actually solves the stated requirement and restores the invariant, rather than only making tests pass;
- root-cause validity and repair classification;
- over-modification: changes beyond the frozen `SELECTED_ISSUES`, the approved task decomposition, or the authorized file scope;
- task-decomposition completeness: every task in `tasks.yaml` reached its acceptance conditions, and no required subtask was dropped;
- integration completeness when the pool ran: seams resolved, interfaces consistent, no half-migrated or dead paths left behind;
- architectural soundness: cohesion, layering, dependency direction, and whether the decomposition left duplicated concepts or awkward boundaries;
- introduced risk: regression exposure, public API, persistence, concurrency, backward compatibility, and migration safety;
- security issues, secret exposure, unsafe shell/process behavior, TLS/auth weakening, and path traversal;
- missing or inadequate tests;
- untriaged recurrence-scan findings or leaked diagnostic residue;
- repository-policy and documentation compliance.

Review the issue ledger as well: confirm discovered issues were not silently dropped, selected IDs match the user's choice, non-selected issues were not modified without authority, and every selected issue has focused plus combined verification.

Rank findings `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`. `CRITICAL` and `HIGH` block completion. `MEDIUM` blocks when it materially affects correctness, reliability, security, compatibility, or maintainability.

Produce `review.md` with findings and terminal markers:

- `REVIEW_STATUS: COMPLETE`
- `REVIEW_INDEPENDENCE: INDEPENDENT | LIMITED | UNAVAILABLE`
- `DECISION: PASS | FAIL | BLOCKED`

For `debug` or `repair`, if the required Complex review fails and the total implementation-attempt limit is not exhausted, return with the findings to the phase that owns them: diagnosis for a requirement or repair-direction defect; planning for a decomposition, task-boundary, or acceptance defect; the owning task's implementation for a single-task defect; integration for a cross-task assembly defect. For standalone `review`, report the findings and stop with `DECISION: FAIL` or `BLOCKED`; do not diagnose, edit, or start a repair loop. Completion of a Complex or standalone review requires `DECISION: PASS` and an independence value allowed by the rules above; Tiny and Normal complete from their route-specific verification result and explicitly skip independent review.

## Completion summary

After entry, treat the summary as the incident's single workflow-exit hook. Immediately before the run exits, the user-facing exit response must contain exactly one distinct Markdown section headed exactly `处理总结`. An exit occurs when the selected `debug`, `diagnose`, `repair`, or `review` scope completes, an early-exit rule is satisfied, or when the run ends partial, failed, blocked with no permitted progress, explicitly stopped, or cancelled. This applies in both automatic and single-step modes whether or not any file changed.

Do not emit `处理总结` at entry confirmation, a phase transition checkpoint, a repair-selection or Agent-upgrade menu, a routine progress response, or a resumable pause awaiting the next confirmation. Those are intermediate workflow turns even if the client renders them as a completed assistant response. Emit the section only once, when the overall incident run actually exits. A later resume continues the same unsummarized run; if a paused run is later stopped or cancelled instead, emit the summary at that exit. Entry option **Codex 原生处理** disables this workflow and continues under the default Codex workflow, so it never starts this contract.

The summary must appear in the workflow-exit response itself; an artifact, commentary update, commit message, or earlier phase report does not satisfy the requirement.

Use these visible labels under the section. Write `无` only when absence is confirmed, `未确认` plus the reason when evidence is insufficient, and `不适用` when the field does not apply; never use `无` to hide an unfinished check:

- `运行结果` — mode and exit state: completed (including valid early completion), partial, failed, blocked, stopped, or cancelled; identify the early-exit reason when applicable;
- `发现的问题` — what was observed and the issue IDs or shared root-cause groups it represents; when multiple issues exist, separate fixed, failed/blocked, deferred, duplicate, and not-a-defect IDs;
- `根因` — the confirmed causal chain and violated invariant;
- `修改状态` — exactly `已修改`, `部分修改`, or `未修改`, referring only to changes made by this workflow run; list the principal files or components changed, or state why no modification was made without counting pre-existing user changes;
- `处理方式` — Change Classifier route (`TINY`/`NORMAL`/`COMPLEX`), diagnosis, planning, repair, and integration actions taken, repair type, planning mode, implementation mode with the number of implementers when pooled, execution mode and decisive scheduling reason, and the meaningful behavioral difference; state coordinator-owned Tiny quick verification and route-skipped review explicitly; write `未实施修复` when applicable;
- `验证结果` — focused and regression checks, their outcomes, and the independent-review decision or limitation;
- `子 Agent 结论` — when delegation occurred, identify every dispatched Agent and synthesize its terminal outcome, conclusion, material limitation, and effect on the workflow; in either run-control mode, use every Agent's retained canonical disclosure label and apply the same pre-send gate; for an implementer pool, group members by task ID instead of repeating near-identical outcomes; otherwise write `不适用`;
- `遗留事项` — unresolved, deferred, blocked, partially verified issues, remaining risks, and the concrete next action;
- `交付状态` — whether required documentation was synchronized and whether a commit was created when either is relevant.
- `中间产物清理` — for a normally completed run in either run-control mode, state `已清理` and the exact removed `RUN_ARTIFACT_DIR`, or `失败` with the retained path and reason; for all other exits, state `已保留` and why, or `不适用` when no run artifacts were created.

For multiple selected issues or pooled tasks, group details by issue ID or task ID when their outcomes differ; do not hide a failed issue or task behind an aggregate success statement. Do not claim success from an attempted edit alone: clearly distinguish fixed, partially fixed, unverified, and unresolved issues. Synthesize the final artifacts instead of copying their full contents or repeating earlier progress updates.

### Run artifact cleanup

Cleanup is part of a normal or early `RUN_CONTROL: AUTO` or `RUN_CONTROL: STEP` completion, after every required result has been consumed and the complete `处理总结` has been synthesized in memory, but before sending the workflow-exit response. It does not run for partial, failed, blocked, stopped, cancelled, or paused exits. If no run artifacts were created, report cleanup as not applicable.

Invoke `sh scripts/cleanup-run-artifacts.sh` with the explicit recorded `ARTIFACT_ROOT` and `RUN_ARTIFACT_DIR`. The script must validate that both paths are absolute existing directories, neither target is a symbolic link or broad root, and the run directory is exactly one direct child of `<ARTIFACT_ROOT>/multi-agent-incident-resolution/`. Never replace these arguments with a glob, unresolved environment variable, current directory, workspace root, shared namespace directory, or inferred path. The script removes the current run directory and prunes the skill namespace directory only when it becomes empty; it never removes `ARTIFACT_ROOT`.

After cleanup, perform a read-only existence check of the exact run directory. Report `中间产物清理: 已清理（<RUN_ARTIFACT_DIR>）` only when it is absent. If validation or deletion fails, do not broaden the target or retry with a less restrictive command; report `中间产物清理: 失败` with the retained exact path and concise reason. Cleanup failure changes the completed run's exit state to partial because the user-requested lifecycle is incomplete, while preserving all repair and verification conclusions already synthesized.

## Git checkpoint policy

Git history is evidence, not a disposable checkpoint mechanism.

- Record status and diff before edits and after each phase that mutates files.
- Do not auto-stash user work. If an explicitly authorized operation needs a clean tree, preserve the exact changes in a named stash or patch and report how to recover them.
- Prefer additive revert commits over history rewriting unless the user explicitly requests rewritten history.
- Commit only when the user requested it or repository instructions require it. Keep unrelated changes and independent todo items in separate commits.
