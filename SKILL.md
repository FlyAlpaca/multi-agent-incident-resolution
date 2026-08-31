---
name: multi-agent-incident-resolution
description: Coordinate bounded, evidence-driven incident investigation, diagnosis, approved repair, verification, and independent review. Use for incident logs, failing tests, regressions, bug fixes, multi-issue triage, or explicit diagnose/repair/review workflows; do not use for ordinary feature work without a reported defect.
---

# Multi-Agent Incident Resolution

Resolve incidents without confusing symptoms with root causes or letting repairs outrun evidence and authority.

## Confirm entry and scope

At the first activation for each incident, use the single entry menu in [references/confirmation.md](references/confirmation.md), unless the request already selects **自动全流程**, **单步确认**, or **不进入流程** unambiguously. Before entry is confirmed, do not inspect the repository, run commands, create artifacts, delegate, or edit files. Keep the selection only for the current incident.

All menus and checkpoints follow the single-surface, numbered-choice contract in [references/confirmation.md](references/confirmation.md). A pending decision belongs in `request_user_input` when callable, otherwise in the final response—not in `commentary`.

After entry, infer the narrowest scope unless the user names one:

- `debug`: investigate, diagnose, implement, verify, and independently review;
- `diagnose`: investigate and diagnose without source edits;
- `repair`: implement, verify, and review an existing approved diagnosis;
- `review`: review the current patch or branch without source edits.

A request to explain, inspect, diagnose, or review does not authorize implementation. A request to fix or repair authorizes in-scope local edits and non-destructive tests, subject to repository rules.

Read the applicable parts of [references/workflow.md](references/workflow.md): stages 1–5 for `debug`, 1–2 for `diagnose`, 3–5 for `repair`, and 5 for `review`. Read [references/multi-issue.md](references/multi-issue.md) for `debug` and `diagnose`, and whenever `repair` or `review` contains multiple issues. Read [references/artifacts.md](references/artifacts.md) before creating, validating, or resuming artifacts.

## Establish the safety envelope

Before mutation:

1. Read applicable `AGENTS.md` and repository instructions.
2. When Git is present, capture `git status --short`, the relevant diff, and recent history.
3. Treat existing tracked and untracked changes as user-owned. Do not discard, reset, clean, stash, overwrite, or commit them without exact authorization or a repository requirement.
4. Identify the incident input and pass it to every delegated phase. Pass artifact paths instead of copying large histories.
5. Record expected and observed behavior, trigger, earliest causally relevant failure, relevant code path, repair scope, and acceptance criteria. Mark unknowns as hypotheses.

Investigate additional failures only within the incident's affected surfaces. Give independent root-cause candidates stable issue IDs and merge duplicate symptoms. Adjacent findings do not authorize adjacent fixes.

Never expose credentials or write unredacted secret-bearing output to artifacts. Do not weaken authentication, TLS, permissions, assertions, or other security controls to suppress a failure.

## Classify the repair

Default to `MINIMAL`. Use `STRUCTURAL` only when evidence shows the current data model, state machine, lifecycle ownership, concurrency boundary, API contract, or abstraction cannot enforce the required invariant.

Before choosing `STRUCTURAL`, record why the smallest plausible patch would leave the failure class possible, accumulate special cases, or violate an invariant. If a focused, testable patch removes the root cause, use it.

## Coordinate subagents

The current Agent remains coordinator and owns user confirmations, artifact state, issue selection, contradiction resolution, and workflow exit. Delegation does not grant shared write authority.

| Role | Responsibility | Default route | Write authority |
|---|---|---|---|
| Coordinator | Scope, checkpoints, artifacts, final delivery | current Agent | workflow artifacts and approved coordination actions |
| Investigator | Logs, runtime facts, source paths, reproduction evidence | `gpt-5.6-luna/max` | read-only |
| Diagnostician | Root cause, invariant, classification, smallest repair | `gpt-5.6-sol/medium` | read-only |
| Implementer | Selected repair and focused tests | `gpt-5.6-luna/max` | sole source writer |
| Verifier | Focused, regression, quality, and recurrence checks | `gpt-5.6-luna/max` | read-only |
| Independent reviewer | Adversarial review of final diff and evidence | `gpt-5.6-sol/medium` | read-only |

This skill authorizes subagent delegation in any mode when a concrete, independent phase materially improves evidence, verification, or review and the client supports it.

- Use only roles that add value; do not delegate ceremonially.
- Parallelize independent read-only work, but keep implementation under one writer and never let a reviewer fix its own findings.
- Give each subagent the incident input, repository rules, workspace snapshot, run directory, bounded task, and explicit authority boundary. Prefer short or no history forks for phase-specific routes.
- Use the task-scoped activity channel and multi-signal liveness protocol in [references/workflow.md](references/workflow.md#subagent-liveness-and-result-visibility). A no-progress window may last up to 1800 seconds (30 minutes) before a full health check and checkpoint; a quiet wait or elapsed time alone never justifies interruption.
- Wait for requested subagents, reconcile contradictions, and visibly relay every terminal result before changing phase.

Use the table's routes by default. Any materially stronger or costlier model, effort, or compute mode is an upgrade and requires the immediately preceding numbered confirmation in [references/confirmation.md](references/confirmation.md#agent-upgrade-confirmation). Neither run-control mode waives it. If the user declines, keep the default when it can make progress; otherwise report the limitation. An unavailable default may be replaced by an equivalent or lower route with disclosure; a higher substitute still needs confirmation.

For every actual subagent in either run-control mode, apply the canonical label and pre-send disclosure contract in [references/confirmation.md](references/confirmation.md#subagent-routing-disclosure). In **单步确认** mode, also disclose the next executor at every phase or Agent-switch checkpoint.

## Bound authority and effort

- **Read-only:** inspect files, logs, diffs, history, and configuration.
- **Local validation:** create disposable test output and run non-destructive checks.
- **In-scope repair:** edit requested local code and tests after diagnosis supports the change.
- **Expanded or structural change:** pause when it materially expands the request, changes a public contract, or repository policy requires approval.
- **High-impact action:** obtain explicit confirmation immediately before external writes, deployment, destructive deletion, history rewriting, credential changes, purchases, or production mutation unless that exact action is already authorized.

Do not invent a token budget or claim exact token accounting. Honor explicit budgets. Otherwise bound work by scope: no more than two implementation attempts per selected issue or shared repair direction, one writer, and only useful independent subagents.

## Stop conditions

Stop patching and report the blocker when:

- the same issue or shared repair direction fails twice;
- diagnosis remains low-confidence after targeted investigation and expert escalation;
- reproduction depends on unavailable external state and safe checks are exhausted;
- required authority exceeds the request;
- user changes cannot be preserved safely; or
- verification cannot distinguish a pre-existing or environmental failure from the repair.

Do not hide deterministic failures with retries, longer timeouts, swallowed exceptions, or weaker tests.

## Completion gate

The implementation gate applies only to `debug` or `repair` runs that entered implementation. `diagnose` ends at a valid stage-2 terminal state; standalone `review` ends at a valid stage-5 terminal state.

An implemented repair is complete only when all selected issues have a supported root cause and repair classification, implementation matches the selected scope, focused and combined checks pass, recurrence findings are cleared or fully triaged, diagnostic residue is handled, regressions are explained, and review returns `PASS` with permitted independence. Every discovered, deferred, blocked, or unverified issue and remaining risk must be stated. The detailed stage and marker requirements in [references/workflow.md](references/workflow.md) and [references/artifacts.md](references/artifacts.md) are authoritative.

On workflow exit, lead with exactly one `处理总结` section using [the completion contract](references/workflow.md#completion-summary). For normal completion in either run-control mode, synthesize the summary first and then clean only the validated current `RUN_ARTIFACT_DIR` with `scripts/cleanup-run-artifacts.sh`. Preserve artifacts for partial, failed, blocked, stopped, cancelled, or paused runs.
