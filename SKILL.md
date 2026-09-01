---
name: multi-agent-incident-resolution
description: Coordinate evidence-driven investigation, diagnosis, approved repair, verification, and independent review for complex incidents, regressions, multi-issue failures, or explicitly requested multi-agent diagnose/repair/review workflows. Do not use for routine single-defect fixes or ordinary feature work that does not benefit from staged coordination.
---

# Multi-Agent Incident Resolution

Resolve incidents without confusing symptoms with root causes or letting repairs outrun evidence, scope, or authority.

## Enter and route the workflow

At the first activation for an incident, use the entry menu in [references/confirmation.md](references/confirmation.md), unless the user already selected **自动全流程**, **单步确认**, or **Codex 原生处理** unambiguously. Selecting **Codex 原生处理** disables this skill workflow and continues the original request under the default Codex workflow. Before entry is resolved, do not inspect, delegate, create artifacts, or edit. The choice applies only to the current incident.

After entry, infer the narrowest authorized scope:

- `debug`: investigate, diagnose, implement, verify, and review;
- `diagnose`: investigate and diagnose without source edits;
- `repair`: implement, verify, and review a supplied, current diagnosis;
- `review`: review the current patch or branch without source edits.

Requests to explain, inspect, diagnose, or review do not authorize implementation. Requests to fix or repair authorize in-scope local edits and non-destructive tests after evidence supports the change.

Read only the references required for that scope:

- [workflow.md](references/workflow.md): stages 1–5 for `debug`, 1–2 for `diagnose`, 3–5 for `repair`, and 5 for `review`;
- [multi-issue.md](references/multi-issue.md): `debug`, `diagnose`, or any run with multiple issues;
- [artifacts.md](references/artifacts.md): before creating, validating, or resuming run artifacts;
- [subagent-state.md](references/subagent-state.md): before dispatching or monitoring a subagent.

Before each stage transition, apply the authoritative [early-exit rules](references/workflow.md#early-exit-rules). Do not dispatch work or emit markers for a stage that those rules skip.

## Establish the evidence and safety envelope

Before mutation:

1. Read applicable repository instructions.
2. When Git is present, capture status, relevant diff, and recent history.
3. Treat all pre-existing tracked and untracked changes as user-owned; do not discard, reset, clean, stash, overwrite, or commit them without exact authorization or a repository requirement.
4. Record expected and observed behavior, trigger, earliest causally relevant failure, relevant code path, repair scope, and acceptance criteria. Mark unknowns as hypotheses.

Investigate only the incident's affected surfaces. Give independent root-cause candidates stable issue IDs and merge duplicate symptoms. Adjacent findings do not authorize adjacent fixes. Never expose credentials, write unredacted secret-bearing artifacts, or weaken security controls to suppress a failure.

## Classify the repair

Default to `MINIMAL`. Use `STRUCTURAL` only when evidence shows that the current data model, state machine, lifecycle ownership, concurrency boundary, API contract, or abstraction cannot enforce the required invariant. Record why a focused patch would leave the failure class possible, accumulate special cases, or violate an invariant.

## Coordinate agents

The current Agent remains coordinator and owns user gates, incident scope, artifacts, issue selection, contradiction resolution, and workflow exit. Delegate only when the runtime permits it and an independent phase materially improves evidence, verification, or review.

| Role | Responsibility | Default route | Authority |
|---|---|---|---|
| Investigator | Reproduction, logs, runtime facts, source paths | `gpt-5.6-luna/max` | read-only |
| Diagnostician | Root cause, invariant, classification, repair proposal | `gpt-5.6-sol/medium` | read-only |
| Implementer | Selected repair and focused tests | `gpt-5.6-luna/max` | sole source writer |
| Verifier | Focused, regression, quality, and recurrence checks | `gpt-5.6-luna/max` | read-only |
| Independent reviewer | Adversarial review of final diff and evidence | `gpt-5.6-sol/medium` | read-only |

- `read-only` means no project-source edits; all roles may write their assigned run artifacts, and verification may create repository-prescribed test/build outputs.
- Use only roles that add value. Parallelize independent read-only work; keep implementation under one writer, and never let a reviewer fix its own findings.
- Give every subagent the incident input, repository rules, workspace snapshot, run directory, bounded task, explicit authority boundary, and its assigned state/result paths.
- Apply the routing disclosure and upgrade rules in [confirmation.md](references/confirmation.md) and the state, relay, and terminal-handoff gates in [subagent-state.md](references/subagent-state.md). Wait for requested agents and reconcile contradictions before changing phase.
- Treat the routes above as defaults. An equivalent or lower available route may substitute with disclosure. A higher-cost route needs confirmation unless the user has already explicitly authorized that exact role and configuration for this incident.

## Bound repair effort

Local, non-destructive validation and an evidence-supported in-scope repair need no extra workflow approval beyond the selected run-control mode. Pause when a change materially expands scope, changes a public contract, conflicts with repository policy, or requires a high-impact action such as deployment, external writes, destructive deletion, history rewriting, credential changes, purchases, or production mutation without exact prior authorization.

Allow at most two implementation attempts per selected issue or shared repair direction. Stop and report when the same direction fails twice, diagnosis remains low-confidence after targeted investigation and permitted escalation, required external state is unavailable, authority is insufficient, user changes cannot be preserved, or verification cannot distinguish the repair from a pre-existing/environmental failure. Do not hide deterministic failures with retries, longer timeouts, swallowed exceptions, or weaker tests.

## Complete or exit

The applicable completion rules and terminal markers in [workflow.md](references/workflow.md) and [artifacts.md](references/artifacts.md) are authoritative. An implemented repair is complete only when selected issues have supported diagnoses, implementation matches scope, focused and combined checks pass, recurrence findings and diagnostic residue are resolved or explicitly triaged, and permitted independent review returns `PASS`.

On workflow exit, emit exactly one `处理总结` section using [the completion contract](references/workflow.md#completion-summary). A valid early exit is a completed run, but its exact reason must remain distinguishable from partial or blocked work. After full or early completion, clean only the validated current `RUN_ARTIFACT_DIR` with `scripts/cleanup-run-artifacts.sh`; preserve artifacts for partial, failed, blocked, stopped, cancelled, or paused runs.
