---
name: multi-agent-incident-resolution
description: Route source-changing incident and repair requests through a deterministic Change Classifier, then use the smallest safe path from a bounded tiny fix through combined diagnosis, isolated implementation, risk-scaled verification, and the full multi-Agent workflow for complex repairs. Also supports explicitly requested diagnose and review workflows. Do not use for ordinary feature work or code explanation.
---

# Multi-Agent Incident Resolution

Resolve incidents without confusing symptoms with root causes or letting repairs outrun evidence, scope, or authority.

## Enter and route the workflow

At the first activation for an incident by the entry Agent, use the entry menu in [references/confirmation.md](references/confirmation.md), unless the user already selected **自动全流程**, **单步确认**, or **Codex 原生处理** unambiguously. Before that choice, do not inspect, delegate, create artifacts, classify, or edit. Dispatched execution Agents follow [the run-control handoff](references/subagent-state.md#run-control-handoff) instead of entering the workflow again. Selecting **Codex 原生处理** disables this skill workflow and continues the original request under the default Codex workflow. The choice applies only to the current incident.

🔴 CHECKPOINT · 入口确认：仅入口 Agent 必须先让用户从三选一中明确运行方式，未确认前不得行动；已校验交接元数据的执行 Agent 不得重新触发入口。选择只对本事件有效。

After the entry choice, infer the narrowest authorized scope. For source-changing `debug` or `repair`, apply the non-Agent [Change Classifier](references/change-classifier.md) to a structured change envelope and persist `classification.md` before the selected route starts. Missing or unknown metrics never qualify for `TINY`; diagnose under `NORMAL` and reclassify before any writer. Classification is not a separate user checkpoint and grants no authority.

Use one of these scopes; the classifier applies only to the source-changing ones:

- `debug`: diagnose, implement, integrate when needed, verify, and review when its route requires; `COMPLEX` keeps investigation and planning as separate phases;
- `diagnose`: investigate and diagnose in one read-only assignment without source edits or task planning;
- `repair`: build the route-appropriate task contract, implement, integrate when needed, verify, and review when required, using a supplied current diagnosis and repair selection;
- `review`: review the current patch or branch without source edits.

For a source-changing request, follow the route and monotonic-upgrade rules in [change-classifier.md](references/change-classifier.md); do not infer a route from the user's adjectives. Integration remains topology-dependent: `SINGLE` skips it and `POOLED` requires it.

Requests to explain, inspect, diagnose, or review do not authorize implementation. Requests to fix or repair authorize only in-scope local edits and non-destructive tests after either a complete `TINY` change envelope or the applicable diagnosis supports the change.

Read only the references required for that scope:

- [workflow.md](references/workflow.md): classifier-dependent routes for source-changing `debug`/`repair`, combined read-only diagnosis for `diagnose`, and independent review for `review`;
- [change-classifier.md](references/change-classifier.md): deterministic source-change routing, thresholds, route-specific gates, and monotonic upgrades;
- [multi-issue.md](references/multi-issue.md): `debug`, `diagnose`, or any run with multiple issues;
- [artifacts.md](references/artifacts.md): before creating, validating, or resuming run artifacts;
- [subagent-state.md](references/subagent-state.md): before dispatching or monitoring a subagent.
- [agent-roles.md](docs/agent-roles.md): when composing a handoff or deciding what context a role receives.

🔴 CHECKPOINT · 阶段门禁：每次阶段切换前套用 [early-exit rules](references/workflow.md#early-exit-rules)；被规则跳过的阶段不得派发工作或发出通过标记。

🔴 CHECKPOINT · 上下文重置：`NORMAL` 内联修复契约或 `COMPLEX` 规划完成进入实施前，以及验证失败开启新修复轮次前，由当前协调者按 [phase context reset](references/workflow.md#phase-context-reset) 原子重建 `active-context.md`；未达到 `CONTEXT_STATUS: READY` 不得派发下一阶段。

## Establish the evidence and safety envelope

Before mutation:

1. Read applicable repository instructions.
2. When Git is present, capture status, relevant diff, and recent history.
3. Treat all pre-existing tracked and untracked changes as user-owned; do not discard, reset, clean, stash, overwrite, or commit them without exact authorization or a repository requirement.
4. Record expected and observed behavior, trigger, earliest causally relevant failure, relevant code path, repair scope, and acceptance criteria. Mark unknowns as hypotheses.

Investigate only the incident's affected surfaces. Give independent root-cause candidates stable issue IDs and merge duplicate symptoms. Adjacent findings do not authorize adjacent fixes. Never expose credentials, write unredacted secret-bearing artifacts, or weaken security controls to suppress a failure.

## Classify the repair direction

The entry classifier's `TINY | NORMAL | COMPLEX` result is a process route, not a technical repair classification. During diagnosis, default the repair direction to `MINIMAL`. Use `STRUCTURAL` only when evidence shows that the current data model, state machine, lifecycle ownership, concurrency boundary, API contract, or abstraction cannot enforce the required invariant. Record why a focused patch would leave the failure class possible, accumulate special cases, or violate an invariant.

## Coordinate agents

The current Agent remains coordinator and owns user gates, incident scope, artifacts, issue selection, task contracts, contradiction resolution, `NORMAL` verification, and workflow exit. Delegate only when the runtime permits it and an independent phase materially improves diagnosis, planning, implementation, integration, verification, or review.

`NORMAL` uses a read-only Diagnoser, one Implementer as the sole source writer, and coordinator-owned basic verification. `COMPLEX` retains the full role chain. The route contract and upgrade criteria live in [change-classifier.md](references/change-classifier.md); do not reconstruct them from this summary.

| Role | Responsibility | Default route | Authority |
|---|---|---|---|
| Investigator | `COMPLEX`-only reproduction, logs, runtime facts, and source paths before diagnosis | `gpt-5.6-luna/max` | read-only |
| Diagnoser | Combined investigation and diagnosis for `NORMAL` or standalone `diagnose`; diagnosis from independent evidence for `COMPLEX`; emits the `NORMAL` inline task contract | `gpt-5.6-sol/medium` | read-only |
| Planner | `COMPLEX` repair-closure decomposition, dependencies, execution waves, acceptance criteria, integration strategy, and readiness self-check | `gpt-5.6-luna/max` | read-only |
| Implementer (pool, normally `1 <= N <= 3`) | One assigned repair-closure task from `tasks.yaml` inside its exclusive file scope | `gpt-5.6-luna/max` | sole writer of its own file scope |
| Integrator | Apply the planned integration strategy, merge subtask results, resolve conflicts and interface mismatches, and complete cross-module wiring; it does not choose the implementation execution mode | `gpt-5.6-luna/max` | sole source writer during integration |
| Verifier | `COMPLEX` verification, or escalated `NORMAL` verification after scope expansion, a failed coordinator check, or elevated residual risk | `gpt-5.6-luna/max` | read-only |
| Independent reviewer | Adversarial review of requirements, final code, and verification results | `gpt-5.6-sol/medium` | read-only |

- `read-only` means no project-source edits; all roles may write their assigned run artifacts, and verification may create repository-prescribed test/build outputs.
- Use only roles that add value. Parallelize independent read-only work, and never let a reviewer fix its own findings.
- `NORMAL` records `TASK_CONTRACT_MODE: DIAGNOSER_INLINE`, emits one `tasks.yaml`, and records planning as skipped. A structural, multi-issue, multi-module, migration, deletion, parallel, or pooled need upgrades to `COMPLEX` before planning or writing. Never cross a repair-selection or single-step gate merely because the same Agent retains context.
- Derive `COMPLEX` tasks, waves, `execution_mode`, and the Implementer budget from complete repair closures under [the task-and-pool contract](references/workflow.md#task-and-pool-shape). Multiple tasks, disjoint files, or available slots do not by themselves authorize concurrent dispatch.
- `tasks.yaml` is the write-authority contract. Its creator is the coordinator for `TINY`, the Diagnoser for `NORMAL`, and the Planner for `COMPLEX`. `POOLED` requires later integration within `integration_scope` after every Implementer stops. Apply [the artifact schema](references/artifacts.md#task-contract).
- Verifiers and reviewers report rather than repair. `TINY` uses coordinator-owned quick verification; `NORMAL` uses coordinator-owned basic verification with conditional Verifier escalation; `COMPLEX` keeps delegated verification and independent review separate from writers.
- Keep each handoff task-specific. Before every dispatch, persist and validate the run-control handoff fields required by [subagent-state.md](references/subagent-state.md#run-control-handoff); an incomplete handoff is not dispatchable. While a task is active the coordinator observes without prompting; terminal handoff and worker termination are separate gates governed solely by that protocol.
- Treat the model/effort entries above as defaults. An equivalent or lower available model route may substitute with disclosure. A higher-cost route needs confirmation unless the user already authorized that exact role and configuration for this incident.

## Bound repair effort

🔴 CHECKPOINT · 高影响边界：本地无损验证与有证据支撑的界内修复无需额外审批；但部署、外部写入、破坏性删除、改写历史、凭据变更、采购或生产变更等高影响动作，必须获得明确授权方可越过。

Allow at most two implementation attempts per selected issue, shared repair direction, or pooled subtask; a subtask retry counts toward the limit of the repair direction it belongs to. Classifier upgrades preserve both `REPAIR_ROUND` and attempt counts. Every repair-attributable verification failure starts a new `REPAIR_ROUND` through fresh diagnosis and a refreshed task contract; `COMPLEX` also repeats dedicated planning. A `TINY` quick-validation failure that upgrades to `NORMAL` follows the same rule and does not reset any attempt counter. Stop and report when the same direction fails twice, diagnosis remains low-confidence after targeted investigation and permitted escalation, required external state is unavailable, authority is insufficient, user changes cannot be preserved, or verification cannot distinguish the repair from a pre-existing/environmental failure. Do not hide deterministic failures with retries, longer timeouts, swallowed exceptions, or weaker tests.

## Complete or exit

Apply the completion criteria in [workflow.md](references/workflow.md) and the terminal markers in [artifacts.md](references/artifacts.md); partial or skipped work never becomes an implicit pass.

On workflow exit, emit exactly one `处理总结` section using [the completion contract](references/workflow.md#completion-summary). A valid early exit is a completed run, but its exact reason must remain distinguishable from partial or blocked work. After full or early completion, clean only the validated current `RUN_ARTIFACT_DIR` with `sh scripts/cleanup-run-artifacts.sh`; preserve artifacts for partial, failed, blocked, stopped, cancelled, or paused runs.
