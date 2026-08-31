---
name: multi-agent-incident-resolution
description: Coordinate specialized Agents to investigate incidents, diagnose root causes, implement approved repairs, verify regressions, and independently review delivery with evidence-first staging and bounded authority. Use for incident logs, failing tests, regressions, bug fixes, multi-issue triage, or explicit diagnose/repair/review workflows; do not use for ordinary feature work without a reported defect.
---

# Multi-Agent Incident Resolution

Coordinate a bounded incident workflow without confusing symptoms with root causes or allowing a repair to outrun the evidence.

## Confirm entry and select the scope

Treat workflow scope and run control as two separate choices.

Whenever presenting two or more actionable choices, present them exactly once through one delivery surface, with consecutive labels starting at `1`. Prefer a callable `request_user_input` prompt with at most three explicit choices; otherwise use one numbered textual list, never both for the same decision. Route overflow actions through the defined **更多操作** secondary prompt instead of exceeding the interactive limit. Never present selectable actions only as unnumbered prose or bullets. User input does not have to be numeric: accept a number, an exact label, a client-owned free-form **Other** result, or an unambiguous natural-language equivalent. If the response could map to more than one option, do not guess; show the same numbered choices again and ask for clarification. Apply the detailed output contract in [references/confirmation.md](references/confirmation.md) to every choice prompt, including repair selection.

A checkpoint awaiting a user decision is a control prompt, not a progress update. Never place its decision context or choices in `commentary`. Use `request_user_input` when callable; otherwise place the complete checkpoint and its numbered choices in the non-collapsed final response and end the turn. Never leave the decision in `commentary` followed by an empty final response.

At the first activation for each new incident, apply the single entry menu defined in [references/confirmation.md](references/confirmation.md) unless the activating request already makes the run-control choice explicit. Render that menu exactly once. Do not define, synthesize, summarize, or emit a second entry-choice list from this file.

Do not inspect the repository, spawn agents, create artifacts, run commands, or modify files before entry is confirmed. Remember the choice for the current incident run only. A new incident requires a new entry confirmation. Read [references/confirmation.md](references/confirmation.md) for confirmation and pause semantics.

After entry is confirmed, infer the narrowest workflow scope from the request:

- **debug**: investigate, diagnose, implement, verify, and independently review. Use when the user asks to fix a defect.
- **diagnose**: investigate and diagnose only. Do not modify source code.
- **repair**: implement, verify, and independently review an existing approved diagnosis.
- **review**: review the current patch or branch only. Do not modify source code.

If the user names a mode, preserve it. A request to explain, inspect, diagnose, or review does not authorize implementation. A request to fix or repair authorizes in-scope local edits and non-destructive tests, subject to repository instructions.

For every mode, read the applicable sections of [references/workflow.md](references/workflow.md): all stages for `debug`, stages 1-2 for `diagnose`, stages 3-5 for `repair`, and stage 5 for `review`. A `repair` run may re-enter diagnosis only to refresh stale or missing evidence, or after a failed implementation/review direction; it does not silently broaden into a new full-debug incident. Read [references/multi-issue.md](references/multi-issue.md) for `debug` and `diagnose`, and for `repair` or `review` whenever the artifacts contain multiple issues. Read [references/artifacts.md](references/artifacts.md) before creating, validating, or resuming workflow artifacts.

## Establish the safety envelope

Before any mutation:

1. Read applicable `AGENTS.md` and repository instructions.
2. Capture `git status --short`, the relevant diff, and recent history when Git is present.
3. Treat all existing tracked and untracked changes as user-owned. Do not discard, reset, clean, stash, overwrite, or commit them unless the user explicitly authorized that exact operation or repository instructions require the commit.
4. Identify the supplied incident material. Pass the incident log or reproduction input to every delegated phase; pass artifact paths instead of copying large histories.
5. State expected behavior, observed behavior, trigger, earliest causally relevant failure, relevant code path, repair scope, and acceptance criteria. Mark unknowns as hypotheses.

Investigate beyond the first visible symptom when evidence suggests multiple failures, but stay within the incident's affected surfaces. Discovering an adjacent issue does not authorize fixing it. Give each independent root-cause candidate a stable issue ID and merge duplicate symptoms before diagnosis.

Never expose credentials. Redact tokens and secrets from artifacts and output. Do not weaken authentication, TLS, permissions, assertions, or security controls to make a failure disappear.

## Classify the repair

Default to `MINIMAL`.

Choose `STRUCTURAL` only when evidence shows the current data model, state machine, lifecycle ownership, concurrency boundary, API contract, or abstraction cannot enforce the required invariant. A refactor being cleaner is not evidence.

Before approving `STRUCTURAL`, construct the smallest plausible patch and record why it would leave the failure class possible, require accumulating special cases, or violate an invariant. If a focused minimal patch fully removes the root cause and is testable, use it.

## Agent roles and ownership

This is a multi-Agent workflow, but delegation never grants shared write authority. The current Agent remains the coordinator and owns user confirmations, artifact state, issue selection, contradiction reconciliation, and workflow exit.

| Role | Responsibility | Default route | Write authority |
|---|---|---|---|
| Coordinator | Controls scope, checkpoints, artifacts, and final delivery | current Agent | workflow artifacts and approved coordination actions |
| Investigator | Collects logs, runtime facts, source paths, and reproduction evidence | `gpt-5.6-luna/max` | read-only |
| Diagnostician | Classifies each issue, identifies root cause/invariant, and proposes the smallest repair | `gpt-5.6-sol/medium` | read-only |
| Implementer | Applies the selected repair and focused tests | `gpt-5.6-luna/max` | exactly one writer |
| Verifier | Runs focused, regression, quality, and recurrence checks when delegation adds value | `gpt-5.6-luna/max` | read-only |
| Independent reviewer | Adversarially reviews the final diff and evidence | `gpt-5.6-sol/medium` | read-only |

Use only the roles that materially improve the current phase. Do not spawn Agents for ceremony, do not run concurrent writers, and do not let a reviewer repair its own findings. Every handoff must carry the same incident input, repository instructions, workspace snapshot, artifact directory, bounded task, and explicit read/write/service-control boundary.

## Use agents deliberately

Applicable instructions in this skill authorize subagent delegation in any mode when a concrete, independent phase would materially improve evidence, verification, or review and the client supports it.

- Delegate only concrete, independent work. Prefer parallel agents for read-heavy investigation, environment checks, test analysis, or adversarial review.
- Keep implementation under one writer. Never let multiple agents edit the same working tree concurrently.
- Prefer a final reviewer that is independent of the implementation agent and does not modify source. Apply the bounded no-subagent fallback in [references/workflow.md](references/workflow.md) only when true independence is unavailable.
- If the defect is small and already well evidenced, skip unnecessary parallel investigation. Do not spawn agents merely to satisfy a fixed count.
- Use short or no history forks when selecting a phase-specific model; give the agent the incident input, applicable repository rules, task, and artifact paths.
- Wait for requested agents and reconcile contradictions before moving to the next phase.

Use these default Agent routes:

- read-heavy investigation and verification: `gpt-5.6-luna` with `max` effort;
- implementation: `gpt-5.6-luna` with `max` effort;
- diagnosis and independent review: `gpt-5.6-sol` with `medium` effort.

Treat any move above the applicable role default as an Agent upgrade. This includes moving a Luna role to Terra, Sol, or another more capable tier; raising a Sol role above `medium`; enabling a higher-compute mode; or selecting another configuration that is materially more capable or costly. Before dispatching the upgraded Agent, apply the mandatory numbered confirmation in [references/confirmation.md](references/confirmation.md). **自动全流程** never waives this boundary.

Always display the Agent-upgrade menu immediately before dispatch and wait for the user's response. A model preference or upgrade request stated earlier in the incident may prefill the proposal but never replaces this confirmation. If the user declines an upgrade, keep the role default when it can still make meaningful progress; otherwise stop or report the unresolved limitation instead of silently upgrading.

If a default route is unavailable, use an equivalent or lower configuration and disclose the substitution. Using a materially higher substitute still requires manual confirmation. Preserve an explicit user choice that satisfies these rules; do not abort an otherwise valid local workflow solely because routing metadata changed.

In **单步确认** mode, a phase-transition checkpoint is invalid until it includes the mandatory next-execution disclosure from [references/confirmation.md](references/confirmation.md#stage-by-stage-confirmation-mode). When the main execution owner continues, identify it simply as `当前 Agent`; do not require or infer hidden session model metadata. When one or more subagents will run, state each subagent's role, exact model, reasoning effort, and bounded task before asking for confirmation.

## Bound authority and effort

Treat permissions as action boundaries, not labels that grant new authority:

- **Read-only**: inspect files, logs, diffs, history, and configuration.
- **Local validation**: create disposable test output and run non-destructive checks.
- **In-scope repair**: edit requested local code and tests after diagnosis supports the change.
- **Expanded or structural change**: pause only when it materially expands the user's request, changes a public contract, or repository policy requires approval/documentation.
- **High-impact action**: obtain explicit confirmation immediately before external writes, deployment, destructive deletion, history rewriting, credential changes, purchases, or production mutation unless the user already authorized that exact action.

Do not invent a token budget or claim exact token accounting. Honor explicit user budgets. Otherwise limit work by scope: at most two implementation attempts per selected issue or shared repair direction, one writer, and only the independent agents that materially improve evidence or review.

## Stop conditions

Stop patching and report the blocker when:

- the same issue or shared repair direction fails twice;
- the diagnosis remains low-confidence after targeted investigation and expert escalation;
- reproduction depends on unavailable external state and safe checks are exhausted;
- required authority would expand beyond the user's request;
- existing user changes cannot be safely preserved;
- verification shows a pre-existing or environmental failure that cannot be distinguished from the repair.

Do not add retries, increase timeouts, swallow exceptions, or weaken tests to hide a deterministic failure.

## Repair completion gate

Apply this gate only to `debug` or `repair` runs that entered implementation. A `diagnose` run completes at a valid stage-2 terminal state, and a standalone `review` run completes at a valid stage-5 terminal state; neither must satisfy implementation-only conditions. An implemented repair is complete only when:

1. every discovered issue is diagnosed, explicitly deferred, or marked blocked with a reason;
2. each selected issue has an identified root cause and violated invariant;
3. `MINIMAL` or `STRUCTURAL` is justified per selected issue or shared root-cause group;
4. implementation matches the user's selected repair set and approved scope;
5. the original failure and every selected issue no longer reproduce under relevant checks;
6. focused per-issue tests and combined regression tests pass;
7. the bounded recurrence scan is `CLEAR`, or its findings have `RECURRENCE_TRIAGE_STATUS: COMPLETE`, without silently expanding the selected set;
8. disposable diagnostic residue is absent and every intentionally retained diagnostic change is justified and tested;
9. unexplained regressions are absent or explicitly separated as pre-existing/environmental;
10. review returns `DECISION: PASS` with `REVIEW_INDEPENDENCE: INDEPENDENT`, or with `LIMITED` only under the narrow fallback criteria in the workflow;
11. deferred issues, blocked issues, remaining risks, and unverified assumptions are stated.

Lead the workflow-exit response with the outcome. Immediately before an incident leaves this workflow, emit exactly one visibly labeled `处理总结` section, regardless of mode, whether files changed, or whether the exit is complete, partial, failed, blocked, stopped, or cancelled. This is a workflow-exit hook, not a per-turn or per-step hook: do not emit it at entry confirmation, phase checkpoints, repair or Agent menus, progress updates, or a resumable pause. When nothing changed, explicitly report `修改状态: 未修改` and the reason. Do not treat an unlabeled closing paragraph, an artifact, or an earlier progress update as satisfying this requirement. Apply the single detailed summary contract in [references/workflow.md](references/workflow.md#completion-summary). Cite files with clickable paths when available.
