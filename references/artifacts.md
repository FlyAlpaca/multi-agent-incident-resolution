# Artifact contract

Artifacts are concise decision records. Include exact file paths, symbols, commands, and outcomes; omit essays and repeated repository context. Never include credentials or raw secret-bearing output.

Record `AGENT_TYPE: ENTRY`, `INVOCATION_SOURCE: EXPLICIT | IMPLICIT`, `RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW`, `RUN_CONTROL: AUTO | STEP`, `ENTRY_SELECTION_INDEX: NOT_APPLICABLE | 1 | 2`, `ARTIFACT_ROOT`, and `RUN_ARTIFACT_DIR` in the first artifact for the incident. An explicit manual Skill invocation maps directly to `RUN_CONTROL: AUTO` with `ENTRY_SELECTION_INDEX: NOT_APPLICABLE`; an implicit activation records the displayed menu selection. A source-changing run also records [Change Classifier](change-classifier.md) output in `classification.md`; the classifier has no dispatch or handoff record. Resolve both paths using [the location contract](workflow.md#workspace-and-artifact-location). Entry option `3` disables this workflow before a run starts, so create no Skill artifact for it. When paused, record the last completed phase and exact pending action without marking an unstarted phase complete.

Treat the first artifact and dispatch ledger as workflow metadata, each Agent's reasoning as Agent context, and the bounded assignment as task payload. Workflow state is read from the persisted metadata and validated against current artifacts; never reconstruct it from conversation or model memory.

Record `EARLY_EXIT_REASON` and `EARLY_EXIT_PHASE` in the terminal artifact. Use `NONE` for both on a full run. The reason vocabulary is intentionally specific; do not collapse an unresolved repair, a deferred issue, a declined repair, an already-present change, and an empty review scope into a generic no-change result.

When a menu choice affects workflow state, record both its semantic value and the displayed option number after normalizing the user's input. The user may have replied with text; the stored number represents the numbered menu that was shown, not an input-format requirement. Use `NOT_APPLICABLE` when no menu was rendered.

`REPAIR_SELECTION_INDEX` records the displayed flat-menu choice after runtime-equivalent options are merged and the menu is renumbered. In `AUTO`, no repair menu is rendered, so record `REPAIR_SELECTION_INDEX: NOT_APPLICABLE`; never synthesize a numeric index. In `STEP`, record the displayed positive index. A modification or custom choice leaves `REPAIR_SELECTION: PENDING` until its details are resolved. The semantic `REPAIR_SELECTION` and `SELECTED_ISSUES` remain authoritative; the index must never be reconstructed from an unmerged template.

Maintain one proposal/dispatch ledger. Give every proposal or dispatch a stable record ID and update that record in place. Include default-route dispatches and upgrades that were defaulted, customized, cancelled, or never dispatched.

Each record contains:

- identity and routing: phase, role, current Change Classifier route, default route, proposed and effective model/effort, canonical disclosure label, reason, and `runtime_agent_id` written immediately after a successful dispatch returns its runtime identity and before the coordinator begins observation;
- run-control handoff: the canonical metadata block required and validated by [subagent-state.md](subagent-state.md#run-control-handoff);
- assignment: bounded task, high-level steps/milestones, expected result/artifact, canonical state path plus optional events path, terminal handoff states, and the obligation to end the subagent turn immediately after handoff;
- channel guards: any client transport limits for dispatch/result messages, kept separate from state and timeout decisions;
- observation plan and decisions: environment-derived `dispatch_started_at`, initial wait, health-check cadence, credible next milestone, and coordinator-owned `OBSERVED_STATUS: NORMAL | FORCE_TERMINATION_ELIGIBLE`. At every observation refresh record `last_observed_at`, the state-derived `last_meaningful_progress`, numeric `elapsed_without_progress_seconds`, and derived `force_termination_eligible_after`. Before an active-task stop also retain the exact eligibility-check command, exit code, JSON decision, `STOP_AUTHORITY: NO_PROGRESS | USER_CANCELLATION | RUNTIME_SAFETY | AUTHORITY_ENFORCEMENT`, and evidence. For terminal reclamation record `STOP_AUTHORITY: TERMINAL_RECLAIM`, its terminal signal, and runtime evidence. Field values and transitions come only from [the lifecycle authority](subagent-state.md#coordinator-observation-and-intervention), not from transport status or copied threshold rules;
- decision and outcome: displayed upgrade choice/index when applicable, dispatch status, result status, `RESULT_CLASSIFICATION: HANDOFF_PROTOCOL_FAILURE` when applicable, terminal conclusion or blocker, optional `RECOVERS_DISPATCH` link, `TASK_HANDOFF_STATUS: ACTIVE | TERMINAL | UNAVAILABLE`, and `USER_RELAY_STATUS: PENDING | RELAYED | NOT_DISPATCHED`;
- execution lifecycle: coordinator-owned `WORKER_LIFECYCLE: ACTIVE | TERMINAL_CONFIRMED | TERMINATION_FAILED` and `TERMINAL_CONFIRMATION: RUNTIME_STATUS | EXPLICIT_CLOSE | EXPLICIT_INTERRUPT | UNAVAILABLE`. Record task handoff separately from runtime termination and apply [the terminal-handling protocol](subagent-state.md#terminal-handling) without restating its stop or reclamation rules in the ledger.

Use numeric units for counts, bytes, and durations. Channel guards are not work limits or timeout evidence. Preserve old rows without inventing historical values. Reuse the stored disclosure label verbatim. Record whether an upgrade used exact prior authorization or a displayed confirmation. Count every above-default proposal in `AGENT_UPGRADE_COUNT`; use `MIXED` when outcomes differ. Set `RELAYED` only after the terminal result is visible in the main conversation.

When resuming a legacy ledger, interpret `TERMINAL_CONFIRMATION: SELF_REPORTED` only as `TASK_HANDOFF_STATUS: TERMINAL`; runtime termination remains unconfirmed until checked. New records never write `SELF_REPORTED` as a terminal-confirmation method.

Use `TERMINAL_CONFIRMATION: UNAVAILABLE` only when runtime termination cannot be queried or established; it cannot support `WORKER_LIFECYCLE: TERMINAL_CONFIRMED`. A worker that is runtime-stopped without a usable handoff uses `RUNTIME_STATUS` for termination and `TASK_HANDOFF_STATUS: UNAVAILABLE` until the abnormal handoff is reconstructed or declared unavailable.

Create one ledger record per dispatched Agent. For an implementer pool, each record carries the task ID, stable pool identifier, wave, exclusive file scope, and acceptance conditions; never collapse several implementers into one record, and never reuse one record when a task is reassigned.

Reserve one `<RUN_ARTIFACT_DIR>/tasks/<task-id>/state.md` path per active dispatch. Write `result.md` at every terminal outcome, including a partial result when failure or cancellation leaves useful evidence, and use `events.jsonl` only for a complex or abnormal task. [The subagent state protocol](subagent-state.md) defines ownership, state, atomic writes, observation, and terminal handling.

Keep all skill-owned records and deliberately redirected intermediate output inside the recorded `RUN_ARTIFACT_DIR`, so cleanup never scans unrelated paths. Repository-prescribed test/build caches and generated output may remain in their normal locations; track and inspect them as possible diagnostic residue. User inputs, project source, runtime data, service logs, and required deliverables are not workflow intermediates and must never be moved into the run directory merely to make cleanup convenient.

Maintain `issue-ledger.md` as the canonical issue inventory for `NORMAL` and `COMPLEX` diagnosis. Each row or section must include stable issue ID, title, status, severity, confidence, root-cause group, dependencies, repair type, approval, selection status, and latest verification result. Never renumber an issue during the same incident. A bounded `TINY` request may use `CHANGE_ID` in `classification.md` and `tasks.yaml` instead of inventing an undiagnosed issue row.

`classification.md` is the canonical route record. It contains the normalized change envelope, classifier status, classification, decisive conditions, source/evidence references for later reclassification, and an append-only upgrade history. Other artifacts reference it rather than copying the envelope or route rationale.

## Active context and repair rounds

`active-context.md` is the coordinator-owned, replaceable allowlist for the next stage. It controls what is loaded, not what evidence is retained. Keep canonical evidence in its existing artifact and reference it by path plus heading, issue ID, task ID, or error ID; do not paste long excerpts or maintain a second summary of the incident.

Every capsule contains:

```text
CONTEXT_VERSION: 1
CONTEXT_GENERATION: <positive integer, incremented on every reset>
REPAIR_ROUND: <positive integer>
CHANGE_CLASSIFICATION: NORMAL | COMPLEX
TARGET_PHASE: DIAGNOSIS | IMPLEMENTATION
RESET_REASON: DIAGNOSIS_TO_IMPLEMENTATION | PLANNING_TO_IMPLEMENTATION | VERIFICATION_FAILURE
SOURCE_REVISION: <Git commit or explicit NO_GIT>
WORKTREE_STATE: <concise status/diff fingerprint or artifact reference>
AUTHORIZED_SCOPE: <selected issue IDs and file/subsystem boundary>
CONSTRAINTS: <concise user, repository, safety, and run-control constraints>
ACTIVE_INVARIANTS: <IDs or precise diagnosis references>
AUTHORITATIVE_INPUTS: <small path-and-anchor allowlist>
FAILURE_INPUTS: <verification error IDs/references, or NOT_APPLICABLE>
TASK_STATE: <current task IDs/statuses or NOT_CREATED>
NEXT_GATE: <one bounded action or checkpoint>
CONTEXT_STATUS: READY | BLOCKED
LIFECYCLE_PROTOCOL: <skill-root>/references/subagent-state.md#coordinator-observation-and-intervention
```

Anything not named by `AUTHORITATIVE_INPUTS` or `FAILURE_INPUTS` is excluded from active context by default. `LIFECYCLE_PROTOCOL` is a mandatory coordinator control reference that survives every capsule rebuild; it is not optional business context. Use references instead of duplicating final plans, constraints, errors, or task entries. Validate the revision, worktree fingerprint, selected issues, referenced paths, and lifecycle protocol immediately before dispatch; drift or a missing authority makes the capsule `BLOCKED` until planning or diagnosis refreshes it. Replace via a validated sibling temporary file and atomic rename so readers never observe a partial capsule.

Maintain `repair-rounds.md` as a compact append-only event ledger. Each row contains round number, event (`OPENED | PASS | VERIFICATION_FAILED | BLOCKED | SUPERSEDED`), baseline revision/worktree fingerprint, diagnosis, task-contract and plan status, implementation attempts consumed, verification artifact/result, and next route. Detailed reasoning stays in the referenced phase artifacts. `TINY` opens round 1 when its task is frozen; `NORMAL` opens it when the Diagnoser freezes its inline task contract; `COMPLEX` opens it when planning starts. A repair-attributable verification failure appends a close event for the current round and an `OPENED` event for the next. Never renumber a round, mutate an earlier event, or reset an attempt counter when the round increments.

## Task contract

`tasks.yaml` is the machine-readable contract between the `TINY` coordinator, `NORMAL` Diagnoser or `COMPLEX` Planner and later implementation, integration, and verification work. Keep it in `RUN_ARTIFACT_DIR` and update it in place; it is the only place that defines what an Implementer may write and how its work is accepted.

```yaml
run:
  artifact_dir: <absolute RUN_ARTIFACT_DIR>
  repair_round: <positive integer>
  change_classification: TINY | NORMAL | COMPLEX
  change_id: CHANGE-001                 # TINY only; NORMAL/COMPLEX use selected_issues
  repair_type: MINIMAL | STRUCTURAL | MIXED
  task_contract_mode: COORDINATOR | DIAGNOSER_INLINE | PLANNER
  implementation_mode: SINGLE | POOLED
  execution_mode: sequential | parallel | mixed
  execution_reason: <why this schedule is safer or more valuable than the alternatives>
  integration_required: false | true
  selected_issues: [ISSUE-001]          # TINY may use [] with change_id instead
  integration_scope: []          # SINGLE; POOLED lists task scopes plus planned shared seams
tasks:
  - id: TASK-001
    title: <short actionable title>
    issue_ids: [ISSUE-001]               # TINY may use [] when change_id is present
    owner: IMPLEMENTER-A          # stable pool identifier; IMPLEMENTER-SINGLE when N=1
    route: gpt-5.6-luna/max
    wave: 1                       # dispatch order; concurrency also requires execution_mode and safety checks
    task_dependencies: []        # task IDs that must complete before this task
    file_scope:                   # exclusive write scope; union of all tasks is the repair scope
      - path/to/file.ts
    read_scope:                   # additional paths the implementer may read
      - path/to/consumer.ts
    acceptance:                   # executable or objectively checkable conditions
      - <command or assertion>
    deliverable: implementation/tasks/TASK-001.md
    status: PENDING | RUNNING | DONE | NO_CHANGE | BLOCKED | FAILED | CANCELLED
    attempt: 0
```

Required properties:

- Task IDs are stable for the whole run; never renumber or reuse one.
- Each task represents one complete repair closure and satisfies [the task-and-pool-shape rules](workflow.md#task-and-pool-shape). Files, modules, functions, and edit locations are scope metadata, not task boundaries; `COMPLEX` `plan.md` carries split justification, while `NORMAL` cannot split.
- For `TINY`, the coordinator creates one task directly from a complete `classification.md` envelope. For `NORMAL`, the Diagnoser creates one task from the inline repair contract in `diagnosis.md`; there is no `plan.md` or stage 3. For `COMPLEX`, the dedicated Planner creates the task set in stage 3.
- `implementation_mode` is a validated summary of task topology: `SINGLE` means exactly one task and one implementer; `POOLED` means at least two tasks and one implementer per task. `execution_mode` independently describes when those tasks may run. `execution_reason` explains why tasks can or cannot overlap; multiple tasks or disjoint files alone never imply `parallel`.
- `run.integration_required` is derived only from task topology: `SINGLE` requires `false`; `POOLED` requires `true`. Keep `integration_scope` empty for `SINGLE`; for `POOLED`, include task scopes plus only the planned shared seams needed by the later Integrator.
- `wave` is the canonical execution order and `task_dependencies` is the canonical dependency list; do not duplicate them in a second graph inside `tasks.yaml`. `sequential` uses one task per wave, `parallel` uses one or more concurrent waves of independent tasks, and `mixed` uses ordered waves with at least one single-task wave and one concurrent wave.
- `file_scope` sets of tasks in the same wave must be disjoint, and no file may be owned by two tasks. Because integration begins only after all implementers stop, `integration_scope` normally contains the union of task scopes plus any planned shared seams; this later-phase overlap does not create concurrent ownership.
- `task_dependencies` references only task IDs from an earlier wave; a task is dispatchable only after every dependency ended as `DONE` or an acceptance-supported `NO_CHANGE` and satisfies [terminal handling](subagent-state.md#terminal-handling). Unrelated parallel work remains independent.
- `acceptance` must be checkable by stage 6 without reinterpretation; a task without acceptance conditions is not dispatchable.
- `status` and `attempt` are updated in place by the coordinator only before dispatch or after the whole active wave stops; `attempt: 0` means not yet dispatched, and the first dispatch sets it to `1`. Never rewrite history to hide a failed task.
- `run.task_contract_mode` records who created the current task contract and must match the selected route: `COORDINATOR` for `TINY`, `DIAGNOSER_INLINE` for `NORMAL`, and `PLANNER` for `COMPLEX`.
- `run.repair_round` identifies the current orchestration cycle. `TINY` opens round 1 when its task is frozen; `NORMAL` opens it when the inline task contract is frozen; `COMPLEX` opens it when planning starts. Advancing it refreshes diagnosis and, for `COMPLEX`, planning state but never resets a task, issue, or shared-direction attempt counter.
- Map a task artifact's `TASK_IMPLEMENTATION_STATUS: COMPLETE` to `tasks.yaml` status `DONE`; the other shared names map directly. `PARTIAL` is terminal evidence but not dependency-complete, so its task-contract status is `BLOCKED` unless a retry is still pending.
- The union of all task `file_scope` entries and `run.integration_scope` stays inside the frozen issue/change scope and authorized file boundary; anything outside returns to triage and selection. An Integrator must not write when `integration_scope` is empty. `TINY` uses `change_id` as the frozen scope when `selected_issues` is empty.

Related run artifacts:

- `diagnosis.md` — the combined evidence and diagnosis record; for `NORMAL` it also carries the inline repair contract;
- `plan.md` — the `COMPLEX`-only human-readable decomposition, dependency, execution-mode, integration, and verification strategy;
- `classification.md` — the normalized change envelope, route decision, and upgrade history;
- `implementation/tasks/<TASK-ID>.md` — one record per dispatched task;
- `implementation.md` — the coordinator-owned aggregate of the implementation phase;
- `integration.md` — the assembly record, required whenever `integration_required` is `true`.
- `verification/round-<NNN>.md` — immutable failure evidence for a non-passing round; `verification.md` remains the current aggregate/index and references these snapshots.

## Resume rules

- `diagnose` produces or refreshes one combined `diagnosis.md` plus `issue-ledger.md`; it must not produce `evidence.md`, `plan.md`, or `tasks.yaml`, and must not edit project source or tests.
- A source-changing `TINY` run may produce `classification.md`, a coordinator-materialized one-task `tasks.yaml`, implementation task evidence, and quick-verification evidence; it must not invent diagnosis or planning artifacts. If the envelope is incomplete, resume through `NORMAL` instead of dispatching the writer.
- `repair` requires a supplied or existing current diagnosis and a repair set frozen under [the multi-issue contract](multi-issue.md#freeze-the-repair-set-by-run-control). Normalize a sufficiently evidenced supplied diagnosis into `diagnosis.md` and `issue-ledger.md`; do not repeat investigation solely because the input did not already use this skill's artifact format. For `NORMAL`, refresh the inline contract and one-task `tasks.yaml` inside the Diagnoser assignment; for `COMPLEX`, derive `plan.md` and `tasks.yaml` in stage 3. Before implementation, require `DIAGNOSIS_STATUS: COMPLETE`, `TASK_CONTRACT_STATUS: COMPLETE`, a non-pending repair selection, and `REPAIR_APPROVED: YES` for every selected issue; only `COMPLEX` additionally requires `PLAN_STATUS: COMPLETE`. If the diagnosis is incomplete or stale relative to the incident input or current diff, return to diagnosis and repair-set resolution; if only a `COMPLEX` decomposition is stale, return to planning, while a stale `NORMAL` task contract returns to the Diagnoser.
- A legacy `tasks.yaml` may be read with `depends_on` as the predecessor of `task_dependencies`, but planning must normalize it to the current field before another implementation dispatch. If `execution_mode` or `execution_reason` is absent, return to planning; never infer permission to run concurrently from legacy waves or disjoint scopes.
- `review` can run without prior artifacts against the current diff, source, and tests. Missing artifacts are then a coverage limitation, not an automatic failure.
- A full `debug` run must not reuse artifacts from a different incident or an earlier source state without validating their inputs and Git revision.

## Terminal marker vocabulary

Use applicable markers one per line so humans and simple tooling can verify state:

```text
AGENT_TYPE: ENTRY
INVOCATION_SOURCE: EXPLICIT | IMPLICIT
RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW
RUN_CONTROL: AUTO | STEP
ENTRY_SELECTION_INDEX: NOT_APPLICABLE | 1 | 2
ARTIFACT_ROOT: <absolute project artifact root or system temporary root>
RUN_ARTIFACT_DIR: <absolute collision-safe directory for this incident>
CHANGE_ID: <stable change id for TINY, or NOT_APPLICABLE>
CHANGE_CLASSIFICATION: TINY | NORMAL | COMPLEX | NOT_APPLICABLE
CHANGE_CLASSIFIER_STATUS: COMPLETE | INCOMPLETE | UPGRADED | NOT_APPLICABLE
REPAIR_ROUND: <positive integer>
CONTEXT_GENERATION: <positive integer>
CONTEXT_STATUS: READY | BLOCKED

EVIDENCE_STATUS: COMPLETE | BLOCKED
ISSUE_DISCOVERY_STATUS: COMPLETE | BOUNDED | BLOCKED
ISSUES_FOUND: <non-negative integer>

EARLY_EXIT_REASON: NONE | NO_ISSUE | NO_ACTIONABLE_REPAIR | NO_REPAIR_SELECTED | CHANGE_ALREADY_PRESENT | EMPTY_REVIEW_SCOPE
EARLY_EXIT_PHASE: NONE | INVESTIGATION | DIAGNOSIS | REPAIR_SELECTION | PLANNING | VERIFICATION | REVIEW

DIAGNOSIS_STATUS: COMPLETE | BLOCKED
TASK_CONTRACT_MODE: COORDINATOR | DIAGNOSER_INLINE | PLANNER | NOT_APPLICABLE
TASK_CONTRACT_STATUS: COMPLETE | BLOCKED | SKIPPED
PLANNING_MODE: DEDICATED | SKIPPED
PLAN_STATUS: COMPLETE | BLOCKED | SKIPPED
REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED | UNDETERMINED
CONFIDENCE: HIGH | MEDIUM | LOW | MIXED
REPAIR_APPROVED: YES | PARTIAL | NO

REPAIR_SELECTION: PENDING | RECOMMENDED | ALL | CUSTOM | NONE | NOT_APPLICABLE
REPAIR_SELECTION_INDEX: NOT_APPLICABLE | PENDING | <displayed positive integer>
SELECTED_ISSUES: PENDING | ISSUE-001,ISSUE-002 | NONE

`NO_ACTIONABLE_REPAIR` represents zero eligible approved repairs and does not create an implementation checkpoint. `NO_REPAIR_SELECTED` is reserved for a `STEP` user declining an otherwise eligible repair set; `AUTO` does not record a synthetic “none” choice.

AGENT_UPGRADES: NONE | PENDING | APPROVED | PREAUTHORIZED | DEFAULTED | CUSTOM | MIXED | CANCELLED
AGENT_UPGRADE_COUNT: <non-negative integer>

IMPLEMENTATION_MODE: SINGLE | POOLED
EXECUTION_MODE: sequential | parallel | mixed
IMPLEMENTER_COUNT: <positive integer>
TASKS_TOTAL: <non-negative integer>
TASKS_DONE: <non-negative integer>
IMPLEMENTATION_STATUS: COMPLETE | NO_CHANGE | PARTIAL | BLOCKED
ATTEMPT: 1 | 2 | MIXED

INTEGRATION_REQUIRED: YES | NO
INTEGRATION_STATUS: SKIPPED | COMPLETE | PARTIAL | BLOCKED

VERIFICATION_STATUS: PASS | PARTIAL | FAIL | BLOCKED
VERIFICATION_MODE: QUICK | BASIC | FULL | NOT_APPLICABLE
VERIFICATION_OWNER: COORDINATOR | VERIFIER | NOT_APPLICABLE
VERIFIER_ESCALATION_REASON: NONE | SCOPE_EXPANDED | CHECK_FAILED | RISK_ELEVATED | MIXED | NOT_APPLICABLE
RECURRENCE_SCAN_STATUS: CLEAR | FINDINGS | BLOCKED
RECURRENCE_TRIAGE_STATUS: NOT_NEEDED | PENDING | COMPLETE | BLOCKED
DIAGNOSTIC_RESIDUE_STATUS: CLEAN | RETAINED | BLOCKED

INDEPENDENT_REVIEW: REQUIRED | SKIPPED_BY_ROUTE | NOT_APPLICABLE
REVIEW_STATUS: COMPLETE
REVIEW_INDEPENDENCE: INDEPENDENT | LIMITED | UNAVAILABLE
DECISION: PASS | FAIL | BLOCKED
```

## Required markers by mode

- A source-changing `TINY` route requires run metadata and classifier markers, `TASK_CONTRACT_MODE: COORDINATOR`, `TASK_CONTRACT_STATUS: COMPLETE`, `PLANNING_MODE: SKIPPED`, `PLAN_STATUS: SKIPPED`, one `SINGLE` implementation task, `INTEGRATION_REQUIRED: NO` with `INTEGRATION_STATUS: SKIPPED`, `VERIFICATION_MODE: QUICK`, `VERIFICATION_OWNER: COORDINATOR`, `VERIFIER_ESCALATION_REASON: NOT_APPLICABLE`, and `INDEPENDENT_REVIEW: SKIPPED_BY_ROUTE`. Investigation, diagnosis, issue selection, recurrence, and review markers are not required; do not fabricate them.
- A source-changing `NORMAL` route requires run metadata and classifier markers, combined evidence and diagnosis in `diagnosis.md`, a frozen repair set, `TASK_CONTRACT_MODE: DIAGNOSER_INLINE`, `TASK_CONTRACT_STATUS: COMPLETE`, `PLANNING_MODE: SKIPPED`, `PLAN_STATUS: SKIPPED`, one `SINGLE` implementation task, `INTEGRATION_REQUIRED: NO` with `INTEGRATION_STATUS: SKIPPED`, `VERIFICATION_OWNER`, `VERIFIER_ESCALATION_REASON`, and `INDEPENDENT_REVIEW: SKIPPED_BY_ROUTE`. Use `VERIFICATION_MODE: BASIC` with coordinator ownership by default; use `FULL` with Verifier ownership only after a recorded escalation. It does not require separate `evidence.md` or `plan.md`, and must upgrade before writing if the final envelope contains a `COMPLEX` trigger.
- A source-changing `COMPLEX` route requires run metadata and classifier markers plus investigation, diagnosis, a frozen repair set, `TASK_CONTRACT_MODE: PLANNER`, `TASK_CONTRACT_STATUS: COMPLETE`, planning (`PLANNING_MODE: DEDICATED`, `PLAN_STATUS: COMPLETE`), implementation, verification with `VERIFICATION_OWNER: VERIFIER` and `VERIFIER_ESCALATION_REASON: NOT_APPLICABLE`, recurrence, residue, and independent review. Integration markers follow topology: `SINGLE` skips it and `POOLED` requires it. When `EARLY_EXIT_REASON` is not `NONE`, require only markers for phases actually run plus the terminal early-exit markers.
- `DIAGNOSE` normally requires run metadata plus combined evidence and diagnosis markers in `diagnosis.md`. Record `TASK_CONTRACT_MODE: NOT_APPLICABLE`, `TASK_CONTRACT_STATUS: SKIPPED`, `PLANNING_MODE: SKIPPED`, and `PLAN_STATUS: SKIPPED`. Repair selection may remain `PENDING` or `NONE`; implementation, integration, verification, and review markers are not required. Finishing diagnosis with no actionable repair is normal scope completion, not an early exit, because standalone `diagnose` never included implementation.
- Source-changing `DEBUG` and `REPAIR` runs use the `TINY`, `NORMAL`, or `COMPLEX` marker set above after classification. A diagnosis or selection early exit omits later markers. `CHANGE_ALREADY_PRESENT` still requires implementation and focused-verification markers, but not integration, recurrence, residue, or review markers when this run made no source change.
- `REVIEW` normally requires run metadata plus `REVIEW_STATUS`, `REVIEW_INDEPENDENCE`, and `DECISION`. Earlier-phase markers are optional; when absent, state the resulting coverage limitation. `EMPTY_REVIEW_SCOPE` may stop after resolving the comparison target and confirming its diff is empty; review-result markers are then unnecessary, and no findings may be invented.
- Agent-upgrade aggregate markers and the dispatch table are required whenever an Agent is proposed or dispatched; otherwise `AGENT_UPGRADES: NONE` and count `0` are sufficient. Do not dispatch a later-stage Agent after an early-exit condition is met.
- Every dispatched Agent must have `TASK_HANDOFF_STATUS: TERMINAL | UNAVAILABLE`, a terminal result or explicit interrupted/unavailable status, a concise conclusion or blocker, `USER_RELAY_STATUS: RELAYED`, and `WORKER_LIFECYCLE: TERMINAL_CONFIRMED` before the workflow transitions past that Agent's phase or exits. `TERMINATION_FAILED` or `TERMINAL_CONFIRMATION: UNAVAILABLE` blocks normal completion. Apply the same requirement to dependent-wave release, integration, and verification; unrelated parallel work does not create a global worker-closure gate.

Do not claim a later phase passed when an earlier marker required by the current mode is absent, invalid, or contradicted by the artifact body. A phase skipped by a valid early exit or by the `TINY`/`NORMAL` route contract is not a pass and must remain unmarked; the latter is recorded by `INDEPENDENT_REVIEW: SKIPPED_BY_ROUTE`. Standalone `REVIEW` is not blocked solely because investigation, diagnosis, implementation, or verification artifacts are absent.

For a multi-issue run, the diagnosis markers are aggregate summaries: use `MIXED` when repair types or confidence differ, and `PARTIAL` when only some issues are approved. Per-issue values in `issue-ledger.md` control selection and implementation; an aggregate `YES` never overrides a per-issue `NO`.

Use `ATTEMPT: MIXED` when selected issues or shared repair groups are on different attempt numbers; retain each exact attempt in `issue-ledger.md` and `implementation.md`.

Use `REPAIR_SELECTION: PENDING` for diagnosis-only output or an unresolved `STEP` choice. In `AUTO`, freeze an eligible approved recommendation immediately after complete diagnosis; do not leave it pending or wait for a menu. No task contract may be finalized while selection or selected issues remain `PENDING`; `COMPLEX` stage 3 also cannot begin. `ISSUE_DISCOVERY_STATUS: BOUNDED` means targeted discovery covered the incident's relevant surfaces and intentionally stopped at the declared scope boundary; it is not a claim that the entire repository is defect-free.

`EARLY_EXIT_PHASE: DIAGNOSIS` is stage 2 only; `PLANNING` is stage 3, used when `COMPLEX` planning produced no executable task. `PLANNING_MODE: SKIPPED` and `PLAN_STATUS: SKIPPED` apply to `TINY`, `NORMAL`, and any exit before planning; never use them to hide unfinished required `COMPLEX` planning. Use `TASK_CONTRACT_STATUS: SKIPPED` only when no source-changing task contract was required or reached, such as standalone `diagnose`, standalone `review`, `NO_ISSUE`, `BLOCKED` diagnosis, or `NO_REPAIR_SELECTED`.

`TASK_CONTRACT_MODE` separates task ownership from planning. `DIAGNOSER_INLINE` means the `NORMAL` Diagnoser embedded the simple repair contract in `diagnosis.md` and produced one `tasks.yaml`; it does not create `plan.md`, stage 3, or a Planner identity. If repair selection or a single-step checkpoint interrupts that assignment, the resumed Diagnoser turn still requires its own dispatch-ledger record and task-state path. `PLANNER` requires a separate `COMPLEX` Planner with its own label, task path, and terminal handoff. A `NORMAL` run that can no longer remain inline upgrades to `COMPLEX` and records the reason and new dispatch rather than rewriting the earlier decision. `IMPLEMENTATION_MODE: SINGLE` requires one Implementer, `EXECUTION_MODE: sequential`, `INTEGRATION_REQUIRED: NO`, and `INTEGRATION_STATUS: SKIPPED`; `POOLED` requires `INTEGRATION_REQUIRED: YES` regardless of schedule or actual changed-file count. `TASKS_DONE` counts only accepted tasks, so an incomplete count must be explicitly triaged, deferred, or blocked.

## Evidence quality

Distinguish:

- **fact**: directly observed in source, logs, commands, or tests;
- **inference**: a causal conclusion supported by stated facts;
- **hypothesis**: plausible but not yet confirmed;
- **limitation**: evidence that could not be obtained and why.

When a sandbox or environment may distort networking, process control, timing, permissions, or external services, label the result as environment-specific and follow repository-prescribed checks before declaring the service or credentials invalid.
