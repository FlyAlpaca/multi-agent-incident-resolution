# Subagent state and timeout protocol

Use this protocol for every dispatched subagent. Resolve all paths relative to the current `RUN_ARTIFACT_DIR`:

```text
artifacts/tasks/<task-id>/state.md
artifacts/tasks/<task-id>/result.md
artifacts/tasks/<task-id>/events.jsonl
```

`state.md` is the only routine state file. Write `result.md` when the task reaches a terminal state. Use append-only `events.jsonl` only when a complex or abnormal task needs a diagnostic event history. Do not create heartbeat files, auxiliary status files, or periodic progress reports.

## State writes

Update `state.md` only when there is confirmed activity worth observing, meaningful progress, a lifecycle change, or a need for coordinator or user intervention. Never write on a timer, repeat unchanged content, or manufacture an update to avoid a stale or termination threshold. A state write is not a substitute for work.

Write the complete file to a sibling temporary path, validate the required fields, and atomically rename it over `state.md`. Do not expose a partially written state. Obtain every timestamp from the execution environment, such as `date --iso-8601=seconds`; never estimate, fabricate, infer from log order, or substitute filesystem mtime.

Every `state.md` contains at least:

```text
STATE_VERSION: 1
TASK: <stable task id and short title>
AGENT: <canonical disclosure label>
MODEL: <exact model and effort>
STATUS: PENDING | RUNNING | WAITING | BLOCKED | NEED_INPUT | DONE | FAILED | CANCELLED | STALE_CANDIDATE | FORCE_TERMINATION_ELIGIBLE
PHASE: <current phase>
GOAL: <bounded outcome>
COMPLETED:
- <completed milestone or none>
CURRENT_PROGRESS: <current high-level work>
NEXT_STEP: <next bounded action>
BLOCKER: <none or concise blocker>
last_activity: <environment-derived ISO 8601 timestamp>
last_activity_summary: <confirmed activity>
last_meaningful_progress: <environment-derived ISO 8601 timestamp>
last_meaningful_progress_summary: <substantive change>
NEEDS_COORDINATOR: YES | NO
NEEDS_USER: YES | NO
```

Add the following details when applicable:

- `WAITING`: the exact wait condition, reason, and expected next observable event or estimate when one is defensible;
- `BLOCKED`: blocker cause, attempts already made, and what is needed to proceed;
- `NEED_INPUT`: decision required, available options, and a default recommendation;
- `FAILED` or `CANCELLED`: termination cause, state at termination, retained evidence, and follow-up recommendation.

## Activity and meaningful progress

Keep the two timestamps independent:

- **Activity** means recently confirmed task activity, such as starting or completing a new command or tool operation, starting a test, reading a new relevant file, performing a new analysis operation, or changing lifecycle state. It shows that work is observable; it does not prove advancement.
- **Meaningful Progress** means a substantive change in evidence, knowledge, judgment, task state, or useful output. Examples include obtaining reliable evidence, eliminating a serious root-cause candidate, confirming a causal link, completing a diagnostic step or meaningful test, validating or rejecting a key hypothesis, narrowing scope, producing a useful conclusion or artifact, completing an approved edit, or validating that edit.

Refreshing `last_activity` never implicitly refreshes `last_meaningful_progress`. Do not refresh meaningful progress for time-only writes, repeated reads or commands, identical failures, empty status text, inconclusive browsing or searching, waiting for a command or external resource, or any update made to defeat a timeout.

## Observation and intervention

The coordinator chooses an initial wait and health-check cadence from expected milestones and task dependencies. Cadence is an observation schedule, not a write schedule or deadline. At a health check, read the protocol timestamps from `state.md` and combine them with available Agent status and messages, `result.md`, relevant workspace differences, and process or test signals. Never use file mtime as Activity or Meaningful Progress.

Apply these distinct thresholds:

1. More than 30 minutes without Activity changes the observed status to `STALE_CANDIDATE`. This is an anomaly candidate, not failure or termination authority. Check for a documented long build, test, analysis, data operation, network request, external-service wait, or other credible long-running tool action. Continue when the silence has a reasonable explanation.
2. More than 60 minutes without Meaningful Progress changes the observed status to `FORCE_TERMINATION_ELIGIBLE`. This grants eligibility for a termination decision, not an automatic termination. Perform the final assessment below first.
3. Intervene earlier when evidence already shows a low-value loop, including repeated identical command failures, repeated disproval without a new direction, the same diagnosis cycling, unjustified scope expansion, or mostly irrelevant output. Do not waste resources merely to reach 60 minutes.

For `WAITING`, preserve the task when the condition is explicit and reasonable. For `BLOCKED`, resolve the cause, replan, reassign, use an approved route change, or terminate according to value and authority. For `NEED_INPUT`, enter the applicable coordinator or user gate; do not treat the wait as a stall.

Before force termination, answer all of the following from current evidence:

- Is a reasonable long-running task still active?
- Is there a blocker the coordinator should resolve?
- Is input required?
- Is an explicit external or tool wait still reasonable?
- Is the Agent looping abnormally?
- Is there a credible next direction or remaining completion value?

Continue when a justified path remains. Prefer, as applicable, continued observation, replanning, a non-interrupting pause, reassignment, or an approved model change. Force termination is the last resort and is permitted only after more than 60 minutes without meaningful progress when there is no reasonable long task or wait, no unresolved `BLOCKED` or `NEED_INPUT` state that should be handled, and no remaining useful path.

The coordinator must not ask routine questions such as whether the Agent is alive, current progress, or time remaining when `state.md` already answers them. Do not request a duplicate report. Intervene only for a coordinator/user decision, abnormal or threshold state, evidence conflict, scope expansion, abnormal behavior, or reassignment need.

## Terminal handling

On normal completion, the subagent atomically writes terminal `state.md` and `result.md`. Before an authorized interruption, preserve the current state and useful evidence. After interruption, ensure the retained `state.md` records `CANCELLED` or `FAILED`, the termination cause, last meaningful progress and its summary, state at termination, and follow-up recommendation. If the subagent cannot write this terminal update, the coordinator may finalize the record and must identify that it did so.

Never discard partial evidence because a task was interrupted. Use `state.md`, `result.md`, and retained artifacts to decide whether the evidence remains usable, investigation must restart, or the task should be replanned, reassigned, or routed differently. After consuming any terminal result, relay its canonical label, status, conclusion, strongest evidence, limitations or blocker, and impact on the next phase before transitioning.
