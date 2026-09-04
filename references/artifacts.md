# Artifact contract

Artifacts are concise decision records. Include exact file paths, symbols, commands, and outcomes; omit essays and repeated repository context. Never include credentials or raw secret-bearing output.

Record `AGENT_TYPE: ENTRY`, `RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW`, `RUN_CONTROL: AUTO | STEP`, `ENTRY_SELECTION_INDEX: 1 | 2`, `ARTIFACT_ROOT`, and `RUN_ARTIFACT_DIR` in the first artifact for the incident. Resolve both paths using the discovery and naming contract in [workflow.md](workflow.md#workspace-and-artifact-location). Entry option `3` (**Codex 原生处理**) disables this workflow before a run starts, so do not create an artifact solely to record it; processing continues under the default Codex workflow. When paused, record the last completed phase and exact pending action without marking an unstarted later phase complete.

Treat the first artifact and dispatch ledger as workflow metadata, each Agent's reasoning as Agent context, and the bounded assignment as task payload. Workflow state is read from the persisted metadata and validated against current artifacts; never reconstruct it from conversation or model memory.

Record `EARLY_EXIT_REASON` and `EARLY_EXIT_PHASE` in the terminal artifact. Use `NONE` for both on a full run. The reason vocabulary is intentionally specific; do not collapse an unresolved repair, a deferred issue, a declined repair, an already-present change, and an empty review scope into a generic no-change result.

When a choice affects workflow state, record both its semantic value and the displayed option number after normalizing the user's input. The user may have replied with text; the stored number represents the numbered menu that was shown, not an input-format requirement.

For hierarchical repair menus, `REPAIR_SELECTION_INDEX` records the primary prompt. Selecting **更多操作** leaves `REPAIR_SELECTION: PENDING` and sets `REPAIR_SECONDARY_INDEX: PENDING` until the secondary prompt is resolved. Use `CLIENT_OTHER` when the client-owned free-form option supplies a custom decision without a skill-controlled number; use `NOT_NEEDED` when the primary prompt directly resolves the repair set. The semantic `REPAIR_SELECTION` and `SELECTED_ISSUES` remain authoritative.

Maintain one proposal/dispatch ledger. Give every proposal or dispatch a stable record ID and update that record in place. Include default-route dispatches and upgrades that were defaulted, customized, cancelled, or never dispatched.

Each record contains:

- identity and routing: phase, role, default route, proposed and effective model/effort, canonical disclosure label, and reason;
- run-control handoff: the canonical metadata block required and validated by [subagent-state.md](subagent-state.md#run-control-handoff);
- assignment: bounded task, high-level steps/milestones, expected result/artifact, canonical state path plus optional events path, terminal handoff states, and the obligation to end the subagent turn immediately after handoff;
- channel guards: any client transport limits for dispatch/result messages, kept separate from state and timeout decisions;
- observation plan: initial wait, health-check cadence, credible next milestone, and coordinator-owned `OBSERVED_STATUS: NORMAL | FORCE_TERMINATION_ELIGIBLE`; apply the fixed threshold from [subagent-state.md](subagent-state.md) rather than copying it into each row;
- decision and outcome: displayed upgrade choice/index when applicable, dispatch status, result status, `RESULT_CLASSIFICATION: HANDOFF_PROTOCOL_FAILURE` when applicable, terminal conclusion or blocker, optional `RECOVERS_DISPATCH` link, `TASK_HANDOFF_STATUS: ACTIVE | TERMINAL | UNAVAILABLE`, and `USER_RELAY_STATUS: PENDING | RELAYED | NOT_DISPATCHED`;
- execution lifecycle: coordinator-owned `WORKER_LIFECYCLE: ACTIVE | TERMINAL_CONFIRMED | TERMINATION_FAILED` and `TERMINAL_CONFIRMATION: RUNTIME_STATUS | EXPLICIT_CLOSE | EXPLICIT_INTERRUPT | UNAVAILABLE`. Record task handoff separately from runtime termination and apply [the terminal-handling protocol](subagent-state.md#terminal-handling) without restating its stop or reclamation rules in the ledger.

Use numeric units for counts, bytes, and durations. Channel guards are not work limits or timeout evidence. Preserve old rows without inventing historical values. Reuse the stored disclosure label verbatim. Record whether an upgrade used exact prior authorization or a displayed confirmation. Count every above-default proposal in `AGENT_UPGRADE_COUNT`; use `MIXED` when outcomes differ. Set `RELAYED` only after the terminal result is visible in the main conversation.

When resuming a legacy ledger, interpret `TERMINAL_CONFIRMATION: SELF_REPORTED` only as `TASK_HANDOFF_STATUS: TERMINAL`; runtime termination remains unconfirmed until checked. New records never write `SELF_REPORTED` as a terminal-confirmation method.

Use `TERMINAL_CONFIRMATION: UNAVAILABLE` only when runtime termination cannot be queried or established; it cannot support `WORKER_LIFECYCLE: TERMINAL_CONFIRMED`. A worker that is runtime-stopped without a usable handoff uses `RUNTIME_STATUS` for termination and `TASK_HANDOFF_STATUS: UNAVAILABLE` until the abnormal handoff is reconstructed or declared unavailable.

Create one ledger record per dispatched Agent. For an implementer pool, each record carries the task ID, stable pool identifier, wave, exclusive file scope, and acceptance conditions; never collapse several implementers into one record, and never reuse one record when a task is reassigned.

Reserve one `<RUN_ARTIFACT_DIR>/tasks/<task-id>/state.md` path per active dispatch. Write `result.md` at every terminal outcome, including a partial result when failure or cancellation leaves useful evidence, and use `events.jsonl` only for a complex or abnormal task. [The subagent state protocol](subagent-state.md) defines ownership, state, atomic writes, observation, and terminal handling.

Keep all skill-owned records and deliberately redirected intermediate output inside the recorded `RUN_ARTIFACT_DIR`, so cleanup never scans unrelated paths. Repository-prescribed test/build caches and generated output may remain in their normal locations; track and inspect them as possible diagnostic residue. User inputs, project source, runtime data, service logs, and required deliverables are not workflow intermediates and must never be moved into the run directory merely to make cleanup convenient.

Maintain `issue-ledger.md` as the canonical multi-issue inventory. Each row or section must include stable issue ID, title, status, severity, confidence, root-cause group, dependencies, repair type, approval, selection status, and latest verification result. Never renumber an issue during the same incident.

## Active context and repair rounds

`active-context.md` is the coordinator-owned, replaceable allowlist for the next stage. It controls what is loaded, not what evidence is retained. Keep canonical evidence in its existing artifact and reference it by path plus heading, issue ID, task ID, or error ID; do not paste long excerpts or maintain a second summary of the incident.

Every capsule contains:

```text
CONTEXT_VERSION: 1
CONTEXT_GENERATION: <positive integer, incremented on every reset>
REPAIR_ROUND: <positive integer>
TARGET_PHASE: DIAGNOSIS | IMPLEMENTATION
RESET_REASON: PLANNING_TO_IMPLEMENTATION | VERIFICATION_FAILURE
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
```

Anything not named by `AUTHORITATIVE_INPUTS` or `FAILURE_INPUTS` is excluded from active context by default. Use references instead of duplicating final plans, constraints, errors, or task entries. Validate the revision, worktree fingerprint, selected issues, and referenced paths immediately before dispatch; drift or a missing authority makes the capsule `BLOCKED` until planning or diagnosis refreshes it. Replace via a validated sibling temporary file and atomic rename so readers never observe a partial capsule.

Maintain `repair-rounds.md` as a compact append-only event ledger. Each row contains round number, event (`OPENED | PASS | VERIFICATION_FAILED | BLOCKED | SUPERSEDED`), baseline revision/worktree fingerprint, diagnosis and plan status, implementation attempts consumed, verification artifact/result, and next route. Detailed reasoning stays in the referenced phase artifacts. Round 1 opens when the initially selected repair enters planning; a repair-attributable verification failure appends a close event for the current round and an `OPENED` event for the next. Never renumber a round, mutate an earlier event, or reset an attempt counter when the round increments.

## Task contract

`tasks.yaml` is the machine-readable contract between planning, the implementer pool, integration, and verification. Keep it in `RUN_ARTIFACT_DIR` and update it in place; it is the only place that defines what an implementer may write and how its work is accepted.

```yaml
run:
  artifact_dir: <absolute RUN_ARTIFACT_DIR>
  repair_round: <positive integer>
  repair_type: MINIMAL | STRUCTURAL | MIXED
  implementation_mode: SINGLE | POOLED
  execution_mode: sequential | parallel | mixed
  execution_reason: <why this schedule is safer or more valuable than the alternatives>
  integration_required: false | true
  selected_issues: [ISSUE-001]
  integration_scope:             # later-phase write boundary; task scopes plus planned shared seams
    - path/to/file.ts
    - path/to/shared-seam.ts
tasks:
  - id: TASK-001
    title: <short actionable title>
    issue_ids: [ISSUE-001]
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
- Each task represents one complete repair closure and satisfies [the task-and-pool-shape rules](workflow.md#task-and-pool-shape). Files, modules, functions, and edit locations are scope metadata, not task boundaries; `plan.md` carries the required split justification.
- `implementation_mode` is a validated summary of task topology: `SINGLE` means exactly one task and one implementer; `POOLED` means at least two tasks and one implementer per task. `execution_mode` independently describes when those tasks may run. `execution_reason` explains why tasks can or cannot overlap; multiple tasks or disjoint files alone never imply `parallel`.
- `wave` is the canonical execution order and `task_dependencies` is the canonical dependency list; do not duplicate them in a second graph inside `tasks.yaml`. `sequential` uses one task per wave, `parallel` uses one or more concurrent waves of independent tasks, and `mixed` uses ordered waves with at least one single-task wave and one concurrent wave.
- `file_scope` sets of tasks in the same wave must be disjoint, and no file may be owned by two tasks. Because integration begins only after all implementers stop, `integration_scope` normally contains the union of task scopes plus any planned shared seams; this later-phase overlap does not create concurrent ownership.
- `task_dependencies` references only task IDs from an earlier wave; a task is dispatchable only after every dependency ended as `DONE` or an acceptance-supported `NO_CHANGE` and its worker termination was confirmed.
- `acceptance` must be checkable by stage 6 without reinterpretation; a task without acceptance conditions is not dispatchable.
- `status` and `attempt` are updated in place by the coordinator only before dispatch or after the whole active wave stops; `attempt: 0` means not yet dispatched, and the first dispatch sets it to `1`. Never rewrite history to hide a failed task.
- `run.repair_round` identifies the current orchestration cycle. Advancing it refreshes diagnosis and planning state but never resets a task, issue, or shared-direction attempt counter.
- Map a task artifact's `TASK_IMPLEMENTATION_STATUS: COMPLETE` to `tasks.yaml` status `DONE`; the other shared names map directly. `PARTIAL` is terminal evidence but not dependency-complete, so its task-contract status is `BLOCKED` unless a retry is still pending.
- The union of all task `file_scope` entries and `run.integration_scope` stays inside the frozen `SELECTED_ISSUES` and the authorized file boundary; anything outside returns to triage and selection. An integrator must not write when `integration_scope` is empty.

Related run artifacts:

- `plan.md` — the human-readable decomposition, dependency, execution-mode, integration, and verification strategy;
- `implementation/tasks/<TASK-ID>.md` — one record per dispatched task;
- `implementation.md` — the coordinator-owned aggregate of the implementation phase;
- `integration.md` — the assembly record, required whenever `integration_required` is `true`.
- `verification/round-<NNN>.md` — immutable failure evidence for a non-passing round; `verification.md` remains the current aggregate/index and references these snapshots.

## Resume rules

- `diagnose` may produce or refresh only the workflow artifacts required by stages 1–2, including `evidence.md`, `diagnosis.md`, and `issue-ledger.md`; it must not produce `plan.md` or `tasks.yaml`, and must not edit project source or tests.
- `repair` requires a supplied or existing current diagnosis and a resolved repair selection. Normalize a sufficiently evidenced supplied diagnosis into `diagnosis.md` and `issue-ledger.md`; do not repeat investigation solely because the input did not already use this skill's artifact format. Derive `plan.md` and `tasks.yaml` in stage 3 when they are missing, stale, or inconsistent with the frozen diagnosis and selection; no implementation is dispatchable without them. Before implementation, require `DIAGNOSIS_STATUS: COMPLETE`, `PLAN_STATUS: COMPLETE`, an explicit non-pending repair selection, and `REPAIR_APPROVED: YES` for every selected issue. If the diagnosis is incomplete or stale relative to the incident input or current diff, return to diagnosis and selection; if only the decomposition is stale, return to planning.
- A legacy `tasks.yaml` may be read with `depends_on` as the predecessor of `task_dependencies`, but planning must normalize it to the current field before another implementation dispatch. If `execution_mode` or `execution_reason` is absent, return to planning; never infer permission to run concurrently from legacy waves or disjoint scopes.
- `review` can run without prior artifacts against the current diff, source, and tests. Missing artifacts are then a coverage limitation, not an automatic failure.
- A full `debug` run must not reuse artifacts from a different incident or an earlier source state without validating their inputs and Git revision.

## Terminal marker vocabulary

Use applicable markers one per line so humans and simple tooling can verify state:

```text
AGENT_TYPE: ENTRY
RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW
RUN_CONTROL: AUTO | STEP
ENTRY_SELECTION_INDEX: 1 | 2
ARTIFACT_ROOT: <absolute project artifact root or system temporary root>
RUN_ARTIFACT_DIR: <absolute collision-safe directory for this incident>
REPAIR_ROUND: <positive integer>
CONTEXT_GENERATION: <positive integer>
CONTEXT_STATUS: READY | BLOCKED

EVIDENCE_STATUS: COMPLETE | BLOCKED
ISSUE_DISCOVERY_STATUS: COMPLETE | BOUNDED | BLOCKED
ISSUES_FOUND: <non-negative integer>

EARLY_EXIT_REASON: NONE | NO_ISSUE | NO_ACTIONABLE_REPAIR | NO_REPAIR_SELECTED | CHANGE_ALREADY_PRESENT | EMPTY_REVIEW_SCOPE
EARLY_EXIT_PHASE: NONE | INVESTIGATION | DIAGNOSIS | REPAIR_SELECTION | PLANNING | VERIFICATION | REVIEW

DIAGNOSIS_STATUS: COMPLETE | BLOCKED
PLANNING_MODE: INLINE | DEDICATED | SKIPPED
PLAN_STATUS: COMPLETE | BLOCKED | SKIPPED
REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED | UNDETERMINED
CONFIDENCE: HIGH | MEDIUM | LOW | MIXED
REPAIR_APPROVED: YES | PARTIAL | NO

REPAIR_SELECTION: PENDING | RECOMMENDED | ALL | CUSTOM | NONE
REPAIR_SELECTION_INDEX: PENDING | 1 | 2 | 3 | CLIENT_OTHER
REPAIR_SECONDARY_INDEX: NOT_NEEDED | PENDING | 1 | 2 | 3 | CLIENT_OTHER
SELECTED_ISSUES: PENDING | ISSUE-001,ISSUE-002 | NONE

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
RECURRENCE_SCAN_STATUS: CLEAR | FINDINGS | BLOCKED
RECURRENCE_TRIAGE_STATUS: NOT_NEEDED | PENDING | COMPLETE | BLOCKED
DIAGNOSTIC_RESIDUE_STATUS: CLEAN | RETAINED | BLOCKED

REVIEW_STATUS: COMPLETE
REVIEW_INDEPENDENCE: INDEPENDENT | LIMITED | UNAVAILABLE
DECISION: PASS | FAIL | BLOCKED
```

## Required markers by mode

- `DEBUG` normally requires run metadata and all investigation, diagnosis, repair-selection, planning (`PLANNING_MODE` and `PLAN_STATUS`), implementation, integration, verification, recurrence, residue, and review markers. Planning records `INTEGRATION_REQUIRED: NO` for `SINGLE` and `YES` for `POOLED`; `NO` requires `INTEGRATION_STATUS: SKIPPED`, while `YES` requires a terminal integration result even if some implementation tasks made no change. An integration phase skipped by a valid early exit stays unmarked. When `EARLY_EXIT_REASON` is not `NONE`, require only the markers for phases actually run plus the terminal early-exit markers; do not fabricate skipped-phase markers.
- `DIAGNOSE` normally requires run metadata plus investigation and diagnosis markers. Record repair selection as `PENDING` or `NONE` when it is discussed, but planning, implementation, integration, verification, and review markers are not required; `PLANNING_MODE: SKIPPED` and `PLAN_STATUS: SKIPPED` when they are recorded. If investigation exits with `EARLY_EXIT_REASON: NO_ISSUE`, diagnosis markers are not required. Finishing diagnosis with no actionable repair is normal scope completion, not an early exit, because standalone `diagnose` never included planning or implementation.
- `REPAIR` normally requires run metadata, a validated diagnosis and repair selection from current artifacts, then planning, implementation, integration, verification, recurrence, residue, and review markers. A diagnosis or selection early exit omits later markers. `CHANGE_ALREADY_PRESENT` still requires implementation and focused-verification markers, but not integration, recurrence, residue, or review markers when this run made no source change.
- `REVIEW` normally requires run metadata plus `REVIEW_STATUS`, `REVIEW_INDEPENDENCE`, and `DECISION`. Earlier-phase markers are optional; when absent, state the resulting coverage limitation. `EMPTY_REVIEW_SCOPE` may stop after resolving the comparison target and confirming its diff is empty; review-result markers are then unnecessary, and no findings may be invented.
- Agent-upgrade aggregate markers and the dispatch table are required whenever an Agent is proposed or dispatched; otherwise `AGENT_UPGRADES: NONE` and count `0` are sufficient. Do not dispatch a later-stage Agent after an early-exit condition is met.
- Every dispatched Agent must have `TASK_HANDOFF_STATUS: TERMINAL | UNAVAILABLE`, a terminal result or explicit interrupted/unavailable status, a concise conclusion or blocker, `USER_RELAY_STATUS: RELAYED`, and `WORKER_LIFECYCLE: TERMINAL_CONFIRMED` before the workflow transitions past that Agent's phase or exits. Task handoff evidence is insufficient while the runtime still reports the dispatch as running; `TERMINATION_FAILED` blocks normal completion.

Do not claim a later phase passed when an earlier marker required by the current mode is absent, invalid, or contradicted by the artifact body. A phase skipped by a valid early exit is not a failure and must remain unmarked. Standalone `REVIEW` is not blocked solely because investigation, diagnosis, implementation, or verification artifacts are absent.

For a multi-issue run, the diagnosis markers are aggregate summaries: use `MIXED` when repair types or confidence differ, and `PARTIAL` when only some issues are approved. Per-issue values in `issue-ledger.md` control selection and implementation; an aggregate `YES` never overrides a per-issue `NO`.

Use `ATTEMPT: MIXED` when selected issues or shared repair groups are on different attempt numbers; retain each exact attempt in `issue-ledger.md` and `implementation.md`.

Use `REPAIR_SELECTION: PENDING` for diagnosis-only output before the user chooses a repair set. Stage 3 cannot begin while selection or selected issues remain `PENDING`. `ISSUE_DISCOVERY_STATUS: BOUNDED` means targeted discovery covered the incident's relevant surfaces and intentionally stopped at the declared scope boundary; it is not a claim that the entire repository is defect-free.

`EARLY_EXIT_PHASE: DIAGNOSIS` is stage 2 only; `PLANNING` is stage 3, used when planning produced no executable task. `PLANNING_MODE: SKIPPED` and `PLAN_STATUS: SKIPPED` apply only when planning never ran, such as a `NO_ISSUE` exit, a `BLOCKED` diagnosis, a `NO_REPAIR_SELECTED` exit, a standalone `diagnose`, or a standalone `review`; never use them to hide an unfinished plan.

`PLANNING_MODE: INLINE` means the diagnostician also produced the plan and keeps its original canonical Agent label; it does not create a distinct planner identity. If repair selection or a single-step checkpoint separates stages 2 and 3, the resumed planning turn still requires its own dispatch-ledger record and task-state path. `DEDICATED` means a separate planner Agent was dispatched with its own label, task path, and terminal handoff. Record the mode once before stage 3 starts; a switch from `INLINE` to `DEDICATED` records the switch reason and new dispatch rather than rewriting the earlier decision. `IMPLEMENTATION_MODE: SINGLE` requires `IMPLEMENTER_COUNT: 1`, `EXECUTION_MODE: sequential`, `INTEGRATION_REQUIRED: NO`, and `INTEGRATION_STATUS: SKIPPED`; this is a normal minimal repair, not a degraded one. `POOLED` requires `INTEGRATION_REQUIRED: YES`, independent of its execution mode or how many workers ultimately changed files. `TASKS_DONE` counts only tasks whose acceptance conditions were met, so a run is not complete while `TASKS_DONE` is below `TASKS_TOTAL` unless the remainder is explicitly triaged, deferred, or blocked.

## Evidence quality

Distinguish:

- **fact**: directly observed in source, logs, commands, or tests;
- **inference**: a causal conclusion supported by stated facts;
- **hypothesis**: plausible but not yet confirmed;
- **limitation**: evidence that could not be obtained and why.

When a sandbox or environment may distort networking, process control, timing, permissions, or external services, label the result as environment-specific and follow repository-prescribed checks before declaring the service or credentials invalid.
