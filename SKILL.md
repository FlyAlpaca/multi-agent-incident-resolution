---
name: multi-agent-incident-resolution
description: Coordinate evidence-driven investigation, diagnosis and task planning, a bounded implementer pool, integration, verification, and independent review for complex incidents, regressions, multi-issue failures, large refactors, or explicitly requested multi-agent diagnose/repair/review workflows. Do not use for routine single-defect fixes or ordinary feature work that does not benefit from staged coordination.
---

# Multi-Agent Incident Resolution

Resolve incidents without confusing symptoms with root causes or letting repairs outrun evidence, scope, or authority.

## Enter and route the workflow

At the first activation for an incident, use the entry menu in [references/confirmation.md](references/confirmation.md), unless the user already selected **自动全流程**, **单步确认**, or **Codex 原生处理** unambiguously. Selecting **Codex 原生处理** disables this skill workflow and continues the original request under the default Codex workflow. Before entry is resolved, do not inspect, delegate, create artifacts, or edit. The choice applies only to the current incident.

🔴 CHECKPOINT · 入口确认：必须先让用户从三选一中明确运行方式，未确认前不得行动；选择只对本事件有效。

After entry, infer the narrowest authorized scope:

- `debug`: investigate, diagnose, plan, implement, integrate when needed, verify, and review;
- `diagnose`: investigate and diagnose without source edits or task planning;
- `repair`: plan, implement, integrate when needed, verify, and review a supplied, current diagnosis and repair selection;
- `review`: review the current patch or branch without source edits.

Requests to explain, inspect, diagnose, or review do not authorize implementation. Requests to fix or repair authorize in-scope local edits and non-destructive tests after evidence supports the change.

Read only the references required for that scope:

- [workflow.md](references/workflow.md): stages 1–7 for `debug`, 1–2 for `diagnose`, 4–7 for `repair`, and 7 for `review`;
- [multi-issue.md](references/multi-issue.md): `debug`, `diagnose`, or any run with multiple issues;
- [artifacts.md](references/artifacts.md): before creating, validating, or resuming run artifacts;
- [subagent-state.md](references/subagent-state.md): before dispatching or monitoring a subagent.

🔴 CHECKPOINT · 阶段门禁：每次阶段切换前套用 [early-exit rules](references/workflow.md#early-exit-rules)；被规则跳过的阶段不得派发工作或发出通过标记。

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

The current Agent remains coordinator and owns user gates, incident scope, artifacts, issue selection, task decomposition records, contradiction resolution, and workflow exit. Delegate only when the runtime permits it and an independent phase materially improves evidence, planning, parallel implementation, integration, verification, or review.

The workflow uses seven roles; the implementer may expand into a pool of N parallel workers. Diagnosis and planning are separate stages, but they share one Agent for a minimal repair and split into two Agents only when the change is large enough to need it.

| Role | Responsibility | Default route | Authority |
|---|---|---|---|
| Investigator | Reproduction, logs, runtime facts, source paths | `gpt-5.6-luna/max` | read-only |
| Diagnostician | Root cause, violated invariant, impact scope, classification, blast radius, repair feasibility; also the inline plan for a `MINIMAL` repair | `gpt-5.6-sol/medium` | read-only |
| Planner | Refactor approach, task decomposition, dependency waves, parallel/serial strategy, acceptance criteria, integration strategy; dispatched only in `DEDICATED` mode | `gpt-5.6-luna/max` | read-only |
| Implementer (pool, `N >= 1`) | One assigned subtask from `tasks.yaml` inside its exclusive file scope | `gpt-5.6-luna/max` | sole writer of its own file scope |
| Integrator | Merge subtask results, resolve conflicts and interface mismatches, complete cross-module wiring | `gpt-5.6-luna/max` | sole source writer during integration |
| Verifier | Focused, regression, quality, and recurrence checks against the defined acceptance criteria | `gpt-5.6-luna/max` | read-only |
| Independent reviewer | Adversarial review of requirements, final code, and verification results | `gpt-5.6-sol/medium` | read-only |

- `read-only` means no project-source edits; all roles may write their assigned run artifacts, and verification may create repository-prescribed test/build outputs.
- Use only roles that add value. Parallelize independent read-only work, and never let a reviewer fix its own findings.
- `PLANNING_MODE: INLINE` is the default: the diagnostician itself writes `plan.md` and a one-task `tasks.yaml` in the same dispatch, so a minimal repair never pays for an extra Agent. Switch to `DEDICATED` for `STRUCTURAL`/`MIXED` repairs, multiple selected issues with distinct file scopes, multi-module/migration/deletion work, or a requested parallel implementation.
- An inline planner designs no refactor and creates no waves. When a repair turns out to need more than one task, it stops, records `PLAN_STATUS: BLOCKED`, and hands back so the coordinator can dispatch a dedicated planner.
- The dedicated planner runs after repair selection, in its own context, and only on the frozen repair set. It decides execution, not correctness: it never redesigns the root cause, changes `REPAIR_TYPE`, or reclassifies issues, and it returns to diagnosis with evidence when the diagnosis cannot support a safe decomposition.
- Implementation is `SINGLE` by default: one implementer owns one task covering the whole approved repair. Use a `POOLED` implementation only when `tasks.yaml` yields two or more subtasks with disjoint file scopes and real parallel value, such as `STRUCTURAL`/`MIXED` repairs, multi-module changes, deletion/migration work, or multiple selected issues with non-overlapping scopes.
- No file may be written by more than one implementer at a time. Overlapping scope goes to exactly one task or is deferred to integration; an implementer must not edit outside its assigned file scope.
- Integration runs only when more than one implementer wrote source; otherwise record `INTEGRATION_STATUS: SKIPPED`. The integrator assembles, resolves conflicts, and restores system-level consistency; it does not redesign, does not change acceptance criteria, and returns to planning or diagnosis when assembly reveals missing decomposition or wrong direction.
- The verifier neither merges nor repairs; it verifies and reports. Findings return to implementation for single-task defects, to integration for cross-task assembly defects, to planning for acceptance or decomposition defects, and to diagnosis for requirement or direction defects.
- The independent reviewer must not have implemented or integrated this repair, and judges only the requirements, the final code, and the verification results.
- Keep every Agent's context small and separate: the planner does not inherit the diagnostician's working memory, and an implementer receives only its own task entry, file scope, acceptance criteria, and the evidence that task needs, instead of the full incident history.
- While a dispatched task is active, the coordinator is observation-only: do not send follow-up messages or prompts. Treat task handoff and worker termination as independent gates; when the task enters a terminal handoff state, immediately reclaim any still-running worker without applying the no-progress threshold. Apply the lifecycle-stop exceptions, routing disclosure, state, relay, and terminal-handoff gates in [confirmation.md](references/confirmation.md) and [subagent-state.md](references/subagent-state.md). Wait only for active requested tasks, reclaim terminal workers, and reconcile contradictions before changing phase.
- Treat the routes above as defaults. An equivalent or lower available route may substitute with disclosure. A higher-cost route needs confirmation unless the user has already explicitly authorized that exact role and configuration for this incident.

## Bound repair effort

🔴 CHECKPOINT · 高影响边界：本地无损验证与有证据支撑的界内修复无需额外审批；但部署、外部写入、破坏性删除、改写历史、凭据变更、采购或生产变更等高影响动作，必须获得明确授权方可越过。

Allow at most two implementation attempts per selected issue, shared repair direction, or pooled subtask; a subtask retry counts toward the limit of the repair direction it belongs to. Stop and report when the same direction fails twice, diagnosis remains low-confidence after targeted investigation and permitted escalation, required external state is unavailable, authority is insufficient, user changes cannot be preserved, or verification cannot distinguish the repair from a pre-existing/environmental failure. Do not hide deterministic failures with retries, longer timeouts, swallowed exceptions, or weaker tests.

## 红线（禁止行为）

无论范围、模式或阶段，以下行为一律禁止；具体机制以对应 references 中的权威协议为准，本节能不重复定义。

- 不得在入口选择解决前 inspect、delegate、建工件或编辑；运行方式选择只对本事件有效，不全局持久化。
- 不得丢弃、reset、clean、stash、覆盖或提交用户已有的改动；用户改动视为用户所有，除非获得明确授权或仓库要求。
- 不得让实施 Agent 写入其 `file_scope` 之外的文件，不得让两个写入者同时写同一文件；集成阶段以外不得出现第二个源码写入者。
- 不得让验证或复核 Agent 自行修复它发现的问题：验证只报告，复核只判定，缺陷路由回对应阶段。
- 不得把可疑日志行直接当作根因；不得为凑置信度用重试、更长超时、吞异常或更弱测试掩盖确定性失败（最多每个方向两次尝试，仍失败即停并报）。
- 不得暴露凭据，不得写未脱敏的敏感输出，不得为压制故障削弱安全控制。
- 不得伪造被跳过的阶段为通过；提前结束须保留真实 `EARLY_EXIT_REASON`，未实际运行的阶段保持未标记。
- 不得把 `处理总结` 当作中途 checkpoint 输出；它只在事件真正退出时出现一次。

## Complete or exit

The applicable completion rules and terminal markers in [workflow.md](references/workflow.md) and [artifacts.md](references/artifacts.md) are authoritative. An implemented repair is complete only when selected issues have supported diagnoses, the approved task decomposition is complete or explicitly triaged, implementation matches scope, integration is complete or recorded `SKIPPED`, focused and combined checks pass, recurrence findings and diagnostic residue are resolved or explicitly triaged, and permitted independent review returns `PASS`.

On workflow exit, emit exactly one `处理总结` section using [the completion contract](references/workflow.md#completion-summary). A valid early exit is a completed run, but its exact reason must remain distinguishable from partial or blocked work. After full or early completion, clean only the validated current `RUN_ARTIFACT_DIR` with `scripts/cleanup-run-artifacts.sh`; preserve artifacts for partial, failed, blocked, stopped, cancelled, or paused runs.
