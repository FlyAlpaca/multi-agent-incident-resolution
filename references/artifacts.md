# Artifact contract

Artifacts are concise decision records. Include exact file paths, symbols, commands, and outcomes; omit essays and repeated repository context. Never include credentials or raw secret-bearing output.

Record `RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW`, `RUN_CONTROL: AUTO | STEP`, `ENTRY_SELECTION_INDEX: 1 | 2`, `ARTIFACT_ROOT`, and `RUN_ARTIFACT_DIR` in the first artifact for the incident. Resolve both paths using the discovery and naming contract in [workflow.md](workflow.md#workspace-and-artifact-location). Entry option `3` (**Codex 原生处理**) disables this workflow before a run starts, so do not create an artifact solely to record it; processing continues under the default Codex workflow. When paused, record the last completed phase and exact pending action without marking an unstarted later phase complete.

Record `EARLY_EXIT_REASON` and `EARLY_EXIT_PHASE` in the terminal artifact. Use `NONE` for both on a full run. The reason vocabulary is intentionally specific; do not collapse an unresolved repair, a deferred issue, a declined repair, an already-present change, and an empty review scope into a generic no-change result.

When a choice affects workflow state, record both its semantic value and the displayed option number after normalizing the user's input. The user may have replied with text; the stored number represents the numbered menu that was shown, not an input-format requirement.

For hierarchical repair menus, `REPAIR_SELECTION_INDEX` records the primary prompt. Selecting **更多操作** leaves `REPAIR_SELECTION: PENDING` and sets `REPAIR_SECONDARY_INDEX: PENDING` until the secondary prompt is resolved. Use `CLIENT_OTHER` when the client-owned free-form option supplies a custom decision without a skill-controlled number; use `NOT_NEEDED` when the primary prompt directly resolves the repair set. The semantic `REPAIR_SELECTION` and `SELECTED_ISSUES` remain authoritative.

Maintain one proposal/dispatch ledger. Give every proposal or dispatch a stable record ID and update that record in place. Include default-route dispatches and upgrades that were defaulted, customized, cancelled, or never dispatched.

Each record contains:

- identity and routing: phase, role, default route, proposed and effective model/effort, canonical disclosure label, and reason;
- assignment: bounded task, high-level steps/milestones, expected result/artifact, canonical state path plus optional events path, terminal handoff states, and the obligation to end the subagent turn immediately after handoff;
- channel guards: any client transport limits for dispatch/result messages, kept separate from state and timeout decisions;
- observation plan: initial wait, health-check cadence, credible next milestone, and coordinator-owned `OBSERVED_STATUS: NORMAL | FORCE_TERMINATION_ELIGIBLE`; apply the fixed threshold from [subagent-state.md](subagent-state.md) rather than copying it into each row;
- decision and outcome: displayed upgrade choice/index when applicable, dispatch status, result status, terminal conclusion or blocker, `TASK_HANDOFF_STATUS: ACTIVE | TERMINAL | UNAVAILABLE`, and `USER_RELAY_STATUS: PENDING | RELAYED | NOT_DISPATCHED`;
- execution lifecycle: coordinator-owned `WORKER_LIFECYCLE: ACTIVE | TERMINAL_CONFIRMED | TERMINATION_FAILED` and `TERMINAL_CONFIRMATION: RUNTIME_STATUS | EXPLICIT_CLOSE | EXPLICIT_INTERRUPT | UNAVAILABLE`, governed by [subagent-state.md](subagent-state.md#terminal-handling). Task handoff and worker termination are independent: a terminal result or self-report sets `TASK_HANDOFF_STATUS`, never `TERMINAL_CONFIRMATION`. `EXPLICIT_INTERRUPT` is a lifecycle action, not a message: for an active task it is reserved for explicit user cancellation, an independently enforced runtime/safety/authority stop, or force termination allowed by the fixed no-progress gate; for a terminal task whose worker remains runtime-live, it is an immediate reclamation mechanism that neither requires the threshold nor changes the recorded task outcome.

Use numeric units for counts, bytes, and durations. Channel guards are not work limits or timeout evidence. Preserve old rows without inventing historical values. Reuse the stored disclosure label verbatim. Record whether an upgrade used exact prior authorization or a displayed confirmation. Count every above-default proposal in `AGENT_UPGRADE_COUNT`; use `MIXED` when outcomes differ. Set `RELAYED` only after the terminal result is visible in the main conversation.

When resuming a legacy ledger, interpret `TERMINAL_CONFIRMATION: SELF_REPORTED` only as `TASK_HANDOFF_STATUS: TERMINAL`; runtime termination remains unconfirmed until checked. New records never write `SELF_REPORTED` as a terminal-confirmation method.

Use `TERMINAL_CONFIRMATION: UNAVAILABLE` only when runtime termination cannot be queried or established; it cannot support `WORKER_LIFECYCLE: TERMINAL_CONFIRMED`. A worker that is runtime-stopped without a usable handoff uses `RUNTIME_STATUS` for termination and `TASK_HANDOFF_STATUS: UNAVAILABLE` until the abnormal handoff is reconstructed or declared unavailable.

Reserve one `<RUN_ARTIFACT_DIR>/tasks/<task-id>/state.md` path per active dispatch. Write `result.md` at every terminal outcome, including a partial result when failure or cancellation leaves useful evidence, and use `events.jsonl` only for a complex or abnormal task. [The subagent state protocol](subagent-state.md) defines ownership, state, atomic writes, observation, and terminal handling.

Keep all skill-owned records and deliberately redirected intermediate output inside the recorded `RUN_ARTIFACT_DIR`, so cleanup never scans unrelated paths. Repository-prescribed test/build caches and generated output may remain in their normal locations; track and inspect them as possible diagnostic residue. User inputs, project source, runtime data, service logs, and required deliverables are not workflow intermediates and must never be moved into the run directory merely to make cleanup convenient.

Maintain `issue-ledger.md` as the canonical multi-issue inventory. Each row or section must include stable issue ID, title, status, severity, confidence, root-cause group, dependencies, repair type, approval, selection status, and latest verification result. Never renumber an issue during the same incident.

## Resume rules

- `diagnose` may produce or refresh only the workflow artifacts required by stages 1–2, including `evidence.md`, `diagnosis.md`, and `issue-ledger.md`; it must not edit project source or tests.
- `repair` requires a supplied or existing current diagnosis. Normalize a sufficiently evidenced supplied diagnosis into `diagnosis.md` and `issue-ledger.md`; do not repeat investigation solely because the input did not already use this skill's artifact format. Before implementation, require `DIAGNOSIS_STATUS: COMPLETE`, an explicit non-pending repair selection, and `REPAIR_APPROVED: YES` for every selected issue. If the diagnosis is incomplete or stale relative to the incident input or current diff, return to diagnosis and selection.
- `review` can run without prior artifacts against the current diff, source, and tests. Missing artifacts are then a coverage limitation, not an automatic failure.
- A full `debug` run must not reuse artifacts from a different incident or an earlier source state without validating their inputs and Git revision.

## Terminal marker vocabulary

Use applicable markers one per line so humans and simple tooling can verify state:

```text
RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW
RUN_CONTROL: AUTO | STEP
ENTRY_SELECTION_INDEX: 1 | 2
ARTIFACT_ROOT: <absolute project artifact root or system temporary root>
RUN_ARTIFACT_DIR: <absolute collision-safe directory for this incident>

EVIDENCE_STATUS: COMPLETE | BLOCKED
ISSUE_DISCOVERY_STATUS: COMPLETE | BOUNDED | BLOCKED
ISSUES_FOUND: <non-negative integer>

EARLY_EXIT_REASON: NONE | NO_ISSUE | NO_ACTIONABLE_REPAIR | NO_REPAIR_SELECTED | CHANGE_ALREADY_PRESENT | EMPTY_REVIEW_SCOPE
EARLY_EXIT_PHASE: NONE | INVESTIGATION | DIAGNOSIS | REPAIR_SELECTION | VERIFICATION | REVIEW

DIAGNOSIS_STATUS: COMPLETE | BLOCKED
REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED | UNDETERMINED
CONFIDENCE: HIGH | MEDIUM | LOW | MIXED
REPAIR_APPROVED: YES | PARTIAL | NO

REPAIR_SELECTION: PENDING | RECOMMENDED | ALL | CUSTOM | NONE
REPAIR_SELECTION_INDEX: PENDING | 1 | 2 | 3 | CLIENT_OTHER
REPAIR_SECONDARY_INDEX: NOT_NEEDED | PENDING | 1 | 2 | 3 | CLIENT_OTHER
SELECTED_ISSUES: PENDING | ISSUE-001,ISSUE-002 | NONE

AGENT_UPGRADES: NONE | PENDING | APPROVED | PREAUTHORIZED | DEFAULTED | CUSTOM | MIXED | CANCELLED
AGENT_UPGRADE_COUNT: <non-negative integer>

IMPLEMENTATION_STATUS: COMPLETE | NO_CHANGE | PARTIAL | BLOCKED
ATTEMPT: 1 | 2 | MIXED

VERIFICATION_STATUS: PASS | PARTIAL | FAIL | BLOCKED
RECURRENCE_SCAN_STATUS: CLEAR | FINDINGS | BLOCKED
RECURRENCE_TRIAGE_STATUS: NOT_NEEDED | PENDING | COMPLETE | BLOCKED
DIAGNOSTIC_RESIDUE_STATUS: CLEAN | RETAINED | BLOCKED

REVIEW_STATUS: COMPLETE
REVIEW_INDEPENDENCE: INDEPENDENT | LIMITED | UNAVAILABLE
DECISION: PASS | FAIL | BLOCKED
```

## Required markers by mode

- `DEBUG` normally requires run metadata and all investigation, diagnosis, repair-selection, implementation, verification, recurrence, residue, and review markers. When `EARLY_EXIT_REASON` is not `NONE`, require only the markers for phases actually run plus the terminal early-exit markers; do not fabricate skipped-phase markers.
- `DIAGNOSE` normally requires run metadata plus investigation and diagnosis markers. Record repair selection as `PENDING` or `NONE` when it is discussed, but implementation, verification, and review markers are not required. If investigation exits with `EARLY_EXIT_REASON: NO_ISSUE`, diagnosis markers are not required. Finishing diagnosis with no actionable repair is normal scope completion, not an early exit, because standalone `diagnose` never included implementation.
- `REPAIR` normally requires run metadata, a validated diagnosis and repair selection from current artifacts, then implementation, verification, recurrence, residue, and review markers. A diagnosis or selection early exit omits later markers. `CHANGE_ALREADY_PRESENT` still requires implementation and focused-verification markers, but not recurrence, residue, or review markers when this run made no source change.
- `REVIEW` normally requires run metadata plus `REVIEW_STATUS`, `REVIEW_INDEPENDENCE`, and `DECISION`. Earlier-phase markers are optional; when absent, state the resulting coverage limitation. `EMPTY_REVIEW_SCOPE` may stop after resolving the comparison target and confirming its diff is empty; review-result markers are then unnecessary, and no findings may be invented.
- Agent-upgrade aggregate markers and the dispatch table are required whenever an Agent is proposed or dispatched; otherwise `AGENT_UPGRADES: NONE` and count `0` are sufficient. Do not dispatch a later-stage Agent after an early-exit condition is met.
- Every dispatched Agent must have `TASK_HANDOFF_STATUS: TERMINAL | UNAVAILABLE`, a terminal result or explicit interrupted/unavailable status, a concise conclusion or blocker, `USER_RELAY_STATUS: RELAYED`, and `WORKER_LIFECYCLE: TERMINAL_CONFIRMED` before the workflow transitions past that Agent's phase or exits. Task handoff evidence is insufficient while the runtime still reports the dispatch as running; `TERMINATION_FAILED` blocks normal completion.

Do not claim a later phase passed when an earlier marker required by the current mode is absent, invalid, or contradicted by the artifact body. A phase skipped by a valid early exit is not a failure and must remain unmarked. Standalone `REVIEW` is not blocked solely because investigation, diagnosis, implementation, or verification artifacts are absent.

For a multi-issue run, the diagnosis markers are aggregate summaries: use `MIXED` when repair types or confidence differ, and `PARTIAL` when only some issues are approved. Per-issue values in `issue-ledger.md` control selection and implementation; an aggregate `YES` never overrides a per-issue `NO`.

Use `ATTEMPT: MIXED` when selected issues or shared repair groups are on different attempt numbers; retain each exact attempt in `issue-ledger.md` and `implementation.md`.

Use `REPAIR_SELECTION: PENDING` for diagnosis-only output before the user chooses a repair set. Stage 3 cannot begin while selection or selected issues remain `PENDING`. `ISSUE_DISCOVERY_STATUS: BOUNDED` means targeted discovery covered the incident's relevant surfaces and intentionally stopped at the declared scope boundary; it is not a claim that the entire repository is defect-free.

## Evidence quality

Distinguish:

- **fact**: directly observed in source, logs, commands, or tests;
- **inference**: a causal conclusion supported by stated facts;
- **hypothesis**: plausible but not yet confirmed;
- **limitation**: evidence that could not be obtained and why.

When a sandbox or environment may distort networking, process control, timing, permissions, or external services, label the result as environment-specific and follow repository-prescribed checks before declaring the service or credentials invalid.
