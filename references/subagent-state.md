# Subagent state and timeout protocol

This protocol is the sole authority for dispatched-task state, checkpoints, observation, intervention, and terminal preservation. Resolve these paths under the current `RUN_ARTIFACT_DIR`:

```text
tasks/<task-id>/state.md
tasks/<task-id>/result.md
tasks/<task-id>/events.jsonl
```

The subagent is the normal writer of `state.md`. The coordinator reads it and records observation decisions in the dispatch ledger; it must not rewrite state while the task is active. Use `events.jsonl` only when a complex or abnormal task needs an append-only diagnostic history. Do not create heartbeat, polling, or auxiliary status files.

## Run-control handoff

Agent type is independent of phase role. The Agent that receives the original incident request and owns user gates is `ENTRY`; every dispatched Agent is `EXECUTION`, whether it investigates, diagnoses, plans, implements, integrates, verifies, or reviews. An execution Agent performs its bounded assignment and never initializes the workflow or asks the user to choose a run mode.

Change Classifier runs before any route dispatch as a deterministic coordinator operation. It is not an Agent, receives no run-control handoff, gets no canonical model label, and has no `state.md`, worker lifecycle, or dispatch-ledger record. Do not create a dummy Agent or consume an Agent-upgrade budget for it. The Tiny Implementer still uses the normal handoff and `tasks.yaml` contract; Tiny quick verification is coordinator-owned and creates no Verifier handoff.

Before every dispatch, the coordinator must persist this workflow-metadata block in that dispatch's ledger record and attach the same values plus the record path to the dispatch envelope, separate from the bounded task payload:

```text
WORKFLOW_METADATA:
  LEDGER_RECORD: <path and stable dispatch record id>
  AGENT_TYPE: EXECUTION
  RUN_CONTROL: AUTO | STEP
  ENTRY_SELECTION_INDEX: 1 | 2
  TASK_ID: <stable task id>
TASK_PAYLOAD:
  TASK: <bounded assignment matching TASK_ID>
```

The ledger record is the authority; the dispatch envelope is transport, not workflow memory. Immediately before dispatch, validate that every field exists, uses the allowed value or identifier form above, agrees with the current run record, and identifies the same task as `TASK_PAYLOAD`. `AGENT_TYPE: EXECUTION` establishes subtask status and suppresses entry; `ENTRY_SELECTION_INDEX` proves that entry was resolved, so do not add parallel boolean flags for either fact. Missing, contradictory, or stale metadata blocks dispatch rather than being inferred from conversation history.

Before any task action, the execution Agent reads the referenced ledger record, compares it with `WORKFLOW_METADATA`, and records `HANDOFF_PROTOCOL_STATUS: VALID` in its initial `state.md`. A valid block authorizes only `TASK_PAYLOAD`, not a wider phase or permission. If the block is missing or inconsistent, the Agent performs no business work and no entry prompt: it writes the available terminal evidence with `HANDOFF_PROTOCOL_STATUS: INVALID`, `RESULT_CLASSIFICATION: HANDOFF_PROTOCOL_FAILURE`, and `STATUS: FAILED`, then ends its turn.

The coordinator also classifies a result as `HANDOFF_PROTOCOL_FAILURE`, rather than a business execution failure, when an execution Agent returns the entry menu, asks for a new run-mode choice, or performs no assigned work solely because it treated the subtask as a fresh workflow. Reclaim the worker under [Terminal handling](#terminal-handling) before considering recovery.

For a read-only investigation assignment, the coordinator may recover automatically once: allocate a new dispatch task ID and state path, retain the failed record, create a new ledger record linked by `RECOVERS_DISPATCH`, copy the same bounded assignment, route, and authority, and supply a freshly validated complete metadata block. This recovery does not consume a repair implementation attempt and, when scope and route are unchanged, does not reopen an already resolved stage confirmation. A repeated handoff protocol failure, any write-capable task, or any recovery that changes scope, route, authority, or risk must stop automatic redispatch and return to the applicable coordination or confirmation gate.

Terminal handoff is one-way. When the bounded task finishes or cannot continue without coordinator or user action, the subagent must write `result.md`, enter `DONE`, `BLOCKED`, `NEED_INPUT`, `FAILED`, or `CANCELLED`, return the result to the coordinator, and immediately end its turn. It must not call a wait primitive, remain available for more work, poll, retry, or spin after a terminal handoff. `WAITING` is only for a self-resolving pre-completion condition with a concrete next observable event.

Keep task state and worker runtime state separate:

- **active task**: `PENDING`, `RUNNING`, or `WAITING` in `state.md`;
- **terminal handoff**: `BLOCKED`, `NEED_INPUT`, `DONE`, `FAILED`, or `CANCELLED`, with `result.md` already written;
- **runtime-live worker**: the runtime still reports the dispatch as running, regardless of task state;
- **runtime-stopped worker**: the runtime reports completion/stop, or a supported lifecycle operation has stopped it and that result has been verified.

A terminal handoff does not prove the worker stopped. A terminal worker that remains runtime-live must be reclaimed immediately.

| Task evidence | Worker runtime | Coordinator action |
|---|---|---|
| active | live | observe passively; apply the active-task stop rules only |
| terminal signal | live | reclaim immediately, then verify runtime stop |
| terminal signal | stopped | consume and reconcile the handoff |
| active, missing, or stale | stopped | retain available evidence and finalize an abnormal terminal handoff; do not wait for the no-progress threshold |

## Pooled dispatch and exclusive scope

A dispatch is either a solo task or one member of an implementer pool. Pool rules:

- one `<task-id>` directory per task; never share a task path between two workers, and never reuse a task path for a reassignment;
- dispatch waves in dependency order: start a wave only after every task in earlier waves reached a terminal handoff and its worker was reclaimed; `sequential` waves contain one task, `parallel` uses concurrent waves, and `mixed` may contain both single-task and concurrent waves;
- before a concurrent wave, revalidate [the canonical parallel-safety criteria](workflow.md#execution-mode); if any condition drifted, dispatch nothing from that wave and return to planning;
- every member receives its exclusive `file_scope` from `tasks.yaml`, writes only inside it, and reports any needed out-of-scope write as a blocker instead of performing it; later integrator authority over the aggregate `run.integration_scope` does not expand any implementer's scope;
- the coordinator stays passive for the whole wave, so a scope conflict discovered mid-wave is resolved at integration, or by replanning after the wave is reclaimed, never by messaging an active member;
- a terminal task does not by itself release dependent tasks; wait until its whole wave is terminal and reconciled;
- a member's `result.md` names its task ID, the files actually written, its acceptance-condition self-check, and every seam left for integration.

## Work plan and checkpoints

At task start, divide the assignment into a small number of outcome-oriented work steps and persist the plan in `state.md`. Use enough steps to expose meaningful progress and recovery points; a simple task may need only one or two, while a complex task may need several. Do not turn individual commands, reads, or searches into work steps.

Write a checkpoint after a work step completes and before starting the next one. Also write when the lifecycle state changes or coordinator/user intervention becomes necessary. A checkpoint is an event-driven snapshot, not a heartbeat:

- increment `CHECKPOINT_ID` monotonically;
- mark the completed and current plan steps;
- summarize the conclusion, blocker, and next bounded action;
- refresh `last_meaningful_progress` only when evidence, knowledge, judgment, task state, or a useful artifact changed substantively.

Do not write on a timer, repeat unchanged content, batch several independently completed steps into one late checkpoint, or manufacture progress to avoid an observation threshold. Multiple related tool operations may belong to one step.

Write the complete snapshot to a sibling temporary file, validate required fields, then atomically rename it over `state.md`. Obtain timestamps from the execution environment, for example with `date --iso-8601=seconds`; never estimate them or substitute file mtime.

## State schema

Every new `state.md` contains at least:

```text
STATE_VERSION: 5
TASK: <stable task id and short title>
AGENT: <canonical disclosure label>
MODEL: <exact model and effort>
HANDOFF_PROTOCOL_STATUS: VALID | INVALID
STATUS: PENDING | RUNNING | WAITING | BLOCKED | NEED_INPUT | DONE | FAILED | CANCELLED
PHASE: <current phase>
GOAL: <bounded outcome>
CHECKPOINT_ID: <non-negative integer>

PLAN:
[x] <completed work step>
[>] <current work step>
[ ] <later work step>

CURRENT_PROGRESS: <current conclusion or none yet>
NEXT_STEP: <next bounded action or none>
BLOCKER: <none or concise blocker>
last_meaningful_progress: <environment-derived ISO 8601 timestamp>
last_meaningful_progress_reason: <substantive change or explicit none-yet reason>
NEEDS_COORDINATOR: YES | NO
NEEDS_USER: YES | NO
```

Use ASCII plan markers so simple tooling can parse them. Exactly one step is current while work is active (`PENDING`, `RUNNING`, or `WAITING`); terminal handoff states (`BLOCKED`, `NEED_INPUT`, `DONE`, `FAILED`, or `CANCELLED`) have no current step. `CURRENT_PROGRESS` summarizes conclusions rather than duplicating the plan, and `NEXT_STEP` identifies the immediate action rather than another full plan.

At initialization, validate the run-control handoff first, set `CHECKPOINT_ID: 0`, persist the initial plan, and set `last_meaningful_progress` from the environment-derived start time. State explicitly that no meaningful progress is confirmed yet; handoff validation, initialization, and plan creation are not meaningful progress. A handoff protocol failure instead writes a terminal snapshot without a current plan step.

Add state-specific detail when applicable:

- `WAITING`: exact wait condition, reason, and next observable event or defensible estimate;
- `BLOCKED`: cause, attempted resolution, condition needed to proceed, and retained evidence for terminal handoff;
- `NEED_INPUT`: decision required, available options, recommendation, and retained evidence for terminal handoff;
- long operation: operation, reason, and defensible estimate;
- `FAILED` or `CANCELLED`: cause, retained evidence, state at termination, and follow-up recommendation.

For compatibility, coordinators may read `STATE_VERSION: 1 | 2 | 3 | 4`, including legacy `*_summary` fields and version 4 snapshots without `HANDOFF_PROTOCOL_STATUS`. In version 3 and earlier, do not assume `BLOCKED` or `NEED_INPUT` is terminal without runtime evidence. New writes use version 5; do not invent missing historical values during migration.

## Meaningful progress and observation

`last_meaningful_progress` is the only subagent-owned timestamp used to measure progress freshness. Keep it and its reason in the atomic `state.md` snapshot:

- **Meaningful progress** is a substantive change in evidence, knowledge, judgment, task state, or useful output, such as narrowing the scope, validating or rejecting a key hypothesis, establishing a causal link, completing an approved edit, or validating it.

Repeated reads or commands, identical failures, inconclusive browsing, waiting, and state-only writes never refresh `last_meaningful_progress`. A completed step that produced only a negative or unchanged result may update the plan and checkpoint while preserving the prior meaningful-progress timestamp and reason.

## Coordinator observation and intervention

The coordinator is passive only while a dispatched task is active. The dispatch assignment is the only coordinator-to-subagent message during that interval: do not send a progress reminder, checkpoint request, decision, follow-up task, `send_input`, or equivalent prompt, and never rewrite its `state.md`. Reclaiming a terminal runtime-live worker is mandatory terminal handling, not force termination, and is not subject to the no-progress threshold. This rule applies in both `AUTO` and `STEP` modes.

Choose the initial wait and health-check cadence from expected milestones and dependencies. The cadence controls coordinator observation, not subagent writes or task deadlines. At a health check, use `last_meaningful_progress` from `state.md` as the sole clock for the no-progress threshold, and interpret it with available Agent status/messages, `result.md`, relevant diffs or artifacts, and process/test signals. Never use file mtime as meaningful progress.

Record the coordinator-owned `OBSERVED_STATUS` in the dispatch ledger:

1. `NORMAL` by default.
2. `FORCE_TERMINATION_ELIGIBLE` only after more than 60 minutes without meaningful progress. This permits a termination decision only after the final assessment below.

Before that threshold, absence of a checkpoint or result, a coordinator wait timeout, low-value work, repeated identical failure, an ordinary scope concern, a missing handoff, or suspected lack of responsiveness does not permit a message, lifecycle stop, reassignment, or close for an active task. Record the observation and continue passive waiting. The only earlier stops of an active task are an explicit user cancellation or concrete evidence requiring an independently enforced runtime, safety, or authority stop. Execute that stop directly without first contacting the subagent. A terminal handoff is no longer an active task and must instead be reclaimed immediately under terminal handling below.

Do not overwrite the subagent's lifecycle `STATUS` with an observed status. Do not treat a documented long-running test, build, analysis, data operation, network request, external wait, or reasonable `WAITING` condition as a stall solely because a threshold elapsed. Handle `BLOCKED` and `NEED_INPUT` as terminal handoffs, not stall evidence.

After the threshold, determine from current evidence whether:

- a reasonable long operation or explicit wait remains active;
- the runtime is inconsistent with a terminal `BLOCKED` or `NEED_INPUT` handoff;
- the Agent is looping abnormally; and
- a credible next direction or completion value remains.

Continue passive observation whenever a justified path remains. A runtime-live worker whose task is still active may be force-terminated only as a last resort after the threshold and final assessment show that no reasonable operation or wait remains and no useful path remains. Use the runtime's supported lifecycle stop directly, including its interrupt operation when that is the available stop mechanism; do not send a preparatory or final message, and do not reassign until the runtime confirms termination. The threshold never authorizes a follow-up message or prompt.

Read `state.md` for routine status instead of asking duplicate questions such as whether the Agent is alive, current progress, or time remaining. Do not contact a worker whose task is active for a decision, conflicting evidence, abnormal state, scope change, reassignment, or any other coordination purpose.

## Terminal handling

For every terminal handoff, atomically write `result.md` first, then atomically write the final checkpoint as terminal `state.md`. This ordering ensures that a visible terminal state always has a complete result available. A terminal state has no current plan step; record unfinished steps and limitations explicitly.

Treat either a terminal `state.md` status or a runtime-delivered final result as a terminal signal. On that signal, record `TASK_HANDOFF_STATUS: TERMINAL` and immediately inspect the runtime state. Do not keep waiting merely because the other handoff artifact is missing or stale. If the runtime automatically stopped the worker, that terminal runtime status is sufficient. Otherwise invoke the runtime's supported close, reclaim, or interrupt operation immediately and verify that the worker stopped. This is terminal reclamation—not force termination—so do not wait for the no-progress threshold and do not leave a terminal worker runtime-live. Do not invent a tool name, send a message, interrupt an already stopped worker, or keep polling after terminal status is confirmed. Record the verified method as `TERMINAL_CONFIRMATION: RUNTIME_STATUS | EXPLICIT_CLOSE | EXPLICIT_INTERRUPT` and set `WORKER_LIFECYCLE: TERMINAL_CONFIRMED`. A self-reported handoff is task evidence only and never worker-runtime confirmation. Using an interrupt operation solely to reclaim a terminal worker does not change or reclassify the task's terminal outcome. After the worker stops, consume both handoff artifacts. Record `TERMINATION_FAILED` and block the phase transition when no supported reclamation operation exists, a reclamation attempt fails, or runtime termination cannot be established.

If the runtime reports the worker stopped before any terminal signal, record `TERMINAL_CONFIRMATION: RUNTIME_STATUS` and `WORKER_LIFECYCLE: TERMINAL_CONFIRMED`; do not continue passive waiting or apply the no-progress threshold. Retain available state, messages, diffs, and artifacts, then finalize a `FAILED` handoff after confirming there is no remaining writer. Use `TASK_HANDOFF_STATUS: UNAVAILABLE` only while no defensible terminal result can be reconstructed; otherwise write the coordinator-authored partial `result.md` and terminal `state.md`, identify their authorship, and set `TASK_HANDOFF_STATUS: TERMINAL`.

Before an authorized interruption of an active task, read and retain the current state and useful evidence without rewriting live task files. After the runtime confirms interruption, ensure a partial `result.md` and terminal `state.md` record `CANCELLED` or `FAILED`, the cause, state at termination, last meaningful progress, retained evidence, and recommendation. If the subagent could not write that terminal snapshot, the coordinator may finalize it only after the task is no longer writing and must identify the coordinator-authored update. Likewise, after terminal reclamation, the coordinator may repair a missing or inconsistent handoff artifact only after runtime termination is confirmed; retain the delivered result and preserve the original terminal outcome.

Never discard partial evidence because a task ended abnormally. Use retained state, result, and artifacts to decide whether evidence is reusable or the task needs replanning, reassignment, or a route change. After consuming a terminal result, relay its canonical label, status, conclusion, strongest evidence, limitations or blocker, and effect on the next phase before transitioning.
