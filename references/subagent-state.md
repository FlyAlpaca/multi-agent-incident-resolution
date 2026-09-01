# Subagent state and timeout protocol

This protocol is the sole authority for dispatched-task state, checkpoints, observation, intervention, and terminal preservation. Resolve these paths under the current `RUN_ARTIFACT_DIR`:

```text
tasks/<task-id>/state.md
tasks/<task-id>/result.md
tasks/<task-id>/events.jsonl
```

The subagent is the normal writer of `state.md`. The coordinator reads it and records observation decisions in the dispatch ledger; it must not rewrite a live subagent's state. Use `events.jsonl` only when a complex or abnormal task needs an append-only diagnostic history. Do not create heartbeat, polling, or auxiliary status files.

Completion is a one-way handoff. When the bounded task's acceptance criteria are met, the subagent must write its result, enter `DONE`, return the result to the coordinator, and stop. It must not continue waiting, polling, retrying, or spinning after completion. `WAITING` is only for an unresolved pre-completion condition.

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
STATE_VERSION: 3
TASK: <stable task id and short title>
AGENT: <canonical disclosure label>
MODEL: <exact model and effort>
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

Use ASCII plan markers so simple tooling can parse them. Exactly one step is current while work is running; terminal states have no current step. `CURRENT_PROGRESS` summarizes conclusions rather than duplicating the plan, and `NEXT_STEP` identifies the immediate action rather than another full plan.

At initialization, set `CHECKPOINT_ID: 0`, persist the initial plan, and set `last_meaningful_progress` from the environment-derived start time. State explicitly that no meaningful progress is confirmed yet; initialization and plan creation are not meaningful progress.

Add state-specific detail when applicable:

- `WAITING`: exact wait condition, reason, and next observable event or defensible estimate;
- `BLOCKED`: cause, attempted resolution, and condition needed to proceed;
- `NEED_INPUT`: decision required, available options, and recommendation;
- long operation: operation, reason, and defensible estimate;
- `FAILED` or `CANCELLED`: cause, retained evidence, state at termination, and follow-up recommendation.

For compatibility, coordinators may read `STATE_VERSION: 1 | 2`, including any legacy `*_summary` fields they contain. New writes use version 3 and `last_meaningful_progress_reason`; do not invent missing historical values during migration.

## Meaningful progress and observation

`last_meaningful_progress` is the only subagent-owned timestamp used to measure progress freshness. Keep it and its reason in the atomic `state.md` snapshot:

- **Meaningful progress** is a substantive change in evidence, knowledge, judgment, task state, or useful output, such as narrowing the scope, validating or rejecting a key hypothesis, establishing a causal link, completing an approved edit, or validating it.

Repeated reads or commands, identical failures, inconclusive browsing, waiting, and state-only writes never refresh `last_meaningful_progress`. A completed step that produced only a negative or unchanged result may update the plan and checkpoint while preserving the prior meaningful-progress timestamp and reason.

## Coordinator observation and intervention

Choose the initial wait and health-check cadence from expected milestones and dependencies. The cadence controls coordinator observation, not subagent writes or task deadlines. At a health check, use `last_meaningful_progress` from `state.md` as the sole clock for the no-progress threshold, and interpret it with available Agent status/messages, `result.md`, relevant diffs or artifacts, and process/test signals. Never use file mtime as meaningful progress.

Record the coordinator-owned `OBSERVED_STATUS` in the dispatch ledger:

1. `NORMAL` by default.
2. `FORCE_TERMINATION_ELIGIBLE` after more than 60 minutes without meaningful progress. This permits a termination decision only after the final assessment below.

Do not overwrite the subagent's lifecycle `STATUS` with an observed status. Do not treat a documented long-running test, build, analysis, data operation, network request, external wait, or reasonable `WAITING`, `BLOCKED`, or `NEED_INPUT` condition as a stall solely because a threshold elapsed.

Intervene earlier when evidence already shows a low-value loop, repeated identical failures, unjustified scope expansion, an authority breach, or mostly irrelevant work. Do not wait for a threshold when safety or scope requires action.

Before force termination, determine from current evidence whether:

- a reasonable long operation or explicit wait remains active;
- the coordinator can resolve a blocker;
- coordinator or user input is required;
- the Agent is looping abnormally; and
- a credible next direction or completion value remains.

Continue, replan, pause without interruption, reassign, or use an approved route change whenever a justified path remains. Force termination is a last resort and is allowed only after the meaningful-progress threshold when no reasonable operation or wait remains, no actionable `BLOCKED` or `NEED_INPUT` condition is being ignored, and no useful path remains.

Read `state.md` for routine status instead of asking duplicate questions such as whether the Agent is alive, current progress, or time remaining. Contact the Agent only for a needed decision, conflicting evidence, abnormal or threshold state, scope change, or reassignment.

## Terminal handling

On normal completion, atomically write `result.md` first, then atomically write the final checkpoint as terminal `state.md`. This ordering ensures that a visible terminal state always has a complete result available. A terminal state has no current plan step; record unfinished steps and limitations explicitly.

After observing `DONE`, consume `result.md` and terminal `state.md`, then confirm through the runtime that the dispatch is no longer running. If the runtime exposes an explicit close/reclaim operation, invoke it; if it automatically terminates completed workers, its terminal status is sufficient. Do not invent a tool name, call interruption on an already terminal worker, or keep polling after terminal status is confirmed. Record the evidence and method in the dispatch ledger as `WORKER_LIFECYCLE: TERMINAL_CONFIRMED`. If the runtime still reports the worker as running, use its supported stop operation and verify again; record `TERMINATION_FAILED` and block the phase transition only when a supported stop attempt fails or terminal state cannot be established.

Before an authorized interruption, preserve current state and useful evidence. After interruption, write a partial `result.md` when possible, then ensure `state.md` records `CANCELLED` or `FAILED`, the cause, state at termination, last meaningful progress, retained evidence, and recommendation. If the subagent cannot write the terminal snapshot, the coordinator may finalize it only after the task is no longer writing and must identify the coordinator-authored update.

Never discard partial evidence because a task ended abnormally. Use retained state, result, and artifacts to decide whether evidence is reusable or the task needs replanning, reassignment, or a route change. After consuming a terminal result, relay its canonical label, status, conclusion, strongest evidence, limitations or blocker, and effect on the next phase before transitioning.
