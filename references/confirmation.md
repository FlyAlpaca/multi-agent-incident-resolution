# Entry and stage confirmation

This contract controls user interaction for one incident run. It does not replace or suppress Codex runtime permission, sandbox, or tool approval prompts.

## Numbered choice contract

For every prompt with two or more actions:

1. number skill-supplied choices consecutively from `1`, including structured option labels;
2. keep each number's meaning stable when re-presenting an unresolved prompt;
3. distinguish menu numbers from stable issue IDs such as `ISSUE-003`;
4. show exactly one actionable choice set for the pending decision.

Deliver the complete decision through one surface: put one numbered list containing every available action in the final response and end the turn. Do not hide actions behind a fixed option limit or a secondary menu. Never place a pending decision in `commentary`, duplicate it across surfaces, or follow it with an empty final response. Do not assume an IDE or try to change client mode.

Immediately before rendering a menu, normalize every candidate choice by its actual runtime effect: action type, target set, scope or constraints, and authorized next transition. Merge candidates whose normalized effects are identical even when their labels or source rules differ, then number the remaining choices consecutively. Use one clear combined label, retain all useful explanation, and do not imply a difference that no longer exists. Re-run this normalization whenever the underlying state changes; do not rely only on statically distinct menu templates.

In particular, do not show both **修改/补充** and **其他 / 自定义** in one menu; use one combined action whose description covers the accepted input. Likewise, if two repair choices resolve to the same issue IDs, repair scope, constraints, and next transition, show one repair choice rather than separate labels.

Accept a number, exact label, structured result, or unambiguous natural-language equivalent; multi-select prompts may also use issue IDs. Normalize the choice internally. If input is ambiguous, invalid, or contradictory, take no action and re-display the same menu through the same surface. Custom detail may arrive in the same reply or the following reply and need not be numeric.

## Entry confirmation

This section is the only source of the entry menu for an incident and applies only to the entry Agent. A dispatched execution Agent follows [the run-control handoff](subagent-state.md#run-control-handoff) and never renders this menu. Render it exactly once for each unresolved entry decision. Do not precede or follow it with another run-control list, a paraphrased copy, or a second set of interactive options.

Before taking workflow actions, present these three choices in simplified Chinese:

1. **自动全流程** — 在选定的 `debug`、`diagnose`、`repair` 或 `review` 范围内持续执行，直到完整或提前正常完成、命中停止条件、需要批准高于默认值的 Agent 升级，或到达高影响操作边界；完成后仅自动清理本次运行的中间工件目录。
2. **单步确认** — 每次只执行一个阶段或一批已批准的 Agent，转换到下一阶段前等待确认；完整或提前正常完成后同样仅自动清理本次运行的中间工件目录。
3. **Codex 原生处理** — 停用本 Skill 工作流，并使用默认 Codex 工作流继续处理原请求；保留用户原有的范围与授权，不再应用本 Skill 的工件、阶段、Agent 路由、菜单或处理总结协议。

The visible option label is only **Codex 原生处理**. Its operational semantics are both: disable this skill workflow, then continue the same request with the default Codex workflow. Do not expose the internal English instruction as a label, alias, parenthetical, or additional choice.

If the user already says “自动全流程”, “单步确认”, “Codex 原生处理”, or an unambiguous equivalent in the activating request, adopt it without asking again. An explicit `$multi-agent-incident-resolution` invocation selects the skill but does not by itself select run control.

Do not persist the selection globally. Keep it only for the current incident. If the incident materially changes, ask again.

## Automatic full-flow mode

Proceed through the selected workflow scope without routine stage prompts. End early when an applicable early-exit rule in [workflow.md](workflow.md#early-exit-rules) is satisfied; an early-exit result is terminal, not a new confirmation prompt, and skipped phases must not start. Still pause or stop for:

- a tool or runtime approval required by the client;
- an action requiring new authority under the skill's high-impact boundary;
- a structural change that materially expands the user's request;
- any workflow stop condition;
- a missing user decision that would materially change the result.

Automatic mode is not blanket authorization for deployment, destructive operations, history rewriting, credential changes, external writes, purchases, or production mutation.

When diagnosis finds repair choices, automatic mode pauses and presents the numbered repair menu defined in [multi-issue.md](multi-issue.md) unless the user preselected a repair set in the activating request. Repair selection is a product/scope decision, not a routine stage prompt.

Choosing `PLANNING_MODE`, `POOLED` implementation, dispatching an implementer wave from the approved `tasks.yaml`, or running the conditional integration phase are routing decisions inside the confirmed scope. They still require routing disclosure and any Agent-upgrade confirmation, but they do not need a further stage confirmation in automatic mode while the decomposition stays inside the frozen `SELECTED_ISSUES` and the authorized file boundary.

Both run-control modes pause before an Agent upgrade above the role defaults defined in `SKILL.md`, unless the user has already explicitly authorized that exact role and configuration for this incident. A general preference for quality, escalation, automatic execution, or a model family is not exact authorization.

Full or early completion in either mode includes [run artifact cleanup](workflow.md#run-artifact-cleanup). Entry selection authorizes only deletion of the validated current run directory after scope completion—not shared roots, other runs, source/runtime data, user logs, or artifacts from any other exit state.

## Subagent routing disclosure

This contract applies equally to both run-control modes. Automatic execution removes routine phase confirmations, not routing transparency.

As soon as a route is selected, create and retain one canonical label with the dispatch record:

`<角色或稳定标识>（模型：<精确模型>；推理强度：<精确强度>）`

Before dispatching, emit a visible `commentary` update using `下一步执行：<规范披露标签>；任务：<有界职责>`. For a parallel batch, give one concise sentence per subagent with its own canonical label and bounded task. Do not dispatch until every planned subagent has a canonical label and bounded task.

Give each member of an implementer pool a stable identifier such as `实施 Agent A` and reuse it in its canonical label, its `tasks.yaml` owner, its ledger record, and every later reference. State its task ID and exclusive file scope in the bounded task so the write boundary is visible before dispatch; a pool member without a visible file scope must not be dispatched.

Record the complete dispatch fields required by [artifacts.md](artifacts.md). They include the task plan, canonical `state.md` path, optional `events.jsonl` path when justified, terminal handoff states, immediate terminal-turn exit obligation, and task-specific observation schedule; transport/channel limits are not work limits or timeout decisions.

After dispatch, use the same canonical label verbatim in every user-facing reference to that actual subagent, including progress, substitution, failure, cancellation, terminal relay, planned next execution, and final summary. Label each member of a batch separately. A substitution gets a newly disclosed label; an upgrade still requires confirmation. Generic references to a stage or role catalog are exempt.

Invalid: `验证 Agent 正在运行；之后由独立 Reviewer 复核。`

Valid: `验证 Agent（模型：gpt-5.6-luna；推理强度：max）正在运行；之后由独立复核 Agent（模型：gpt-5.6-sol；推理强度：medium）复核。`

Valid for a pool: `实施 Agent A（模型：gpt-5.6-luna；推理强度：max）负责 TASK-001，写入范围 src/a/；实施 Agent B（模型：gpt-5.6-luna；推理强度：max）负责 TASK-002，写入范围 src/b/；两者文件范围不重叠，完成后由集成员整合。`

## Agent upgrade confirmation

When an upgrade lacks exact prior authorization, show the role, default model/effort, proposed model/effort or compute mode, reason, expected benefit, and additional cost/latency risk. Then present this numbered menu and wait:

1. **确认升级** — authorize only the displayed Agent role and configuration and, in single-step mode, execute the displayed phase or batch;
2. **保持默认** — use the role's default configuration and, in single-step mode, execute the displayed phase or batch if meaningful progress remains possible;
3. **修改/补充/自定义** — choose another model, effort, constraint, or routing approach without dispatching the Agent.
4. **暂停流程** — preserve the current run as resumable and do not emit the exit summary.
5. **结束流程** — exit the incident and emit the required summary.

Keep the same numbers if the answer is ambiguous. Record an exact prior authorization in the dispatch ledger and proceed without duplicating this prompt; a broader or different configuration still requires confirmation.

## Stage-by-stage confirmation mode

Before each phase transition, Agent switch, or parallel Agent batch, show one concise checkpoint in simplified Chinese containing:

- completed phase and its terminal result;
- proposed next phase;
- whether the next phase is read-only, validates locally, or may write;
- intended files, commands, or mutation scope when known;
- current risks, unresolved assumptions, and relevant stop conditions.

When an early-exit rule applies, do not show a checkpoint for the skipped stage. Record the terminal markers and send the single workflow-exit summary. In single-step mode, confirmation of the completed phase does not authorize work removed by that rule.

Immediately before the single numbered choice set, describe the next executor in concise prose rather than a table. Apply the shared routing-disclosure contract:

- when the coordinator itself continues without dispatching a subagent, write `下一步执行：当前 Agent，将负责……`; this coordinator identifier is not a subagent route label and does not require hidden session model metadata;
- when delegating one subagent, write `下一步执行：<规范披露标签>；任务：<有界职责>`;
- for a parallel read-only batch, give one short sentence per subagent using the same canonical label and bounded task.

Do not show the confirmation choices or start the phase until every planned subagent has a canonical label, exact model, reasoning effort, and bounded task. If execution changes between the current Agent and a subagent, or any displayed subagent, model, effort, or task changes before execution, create or revise the affected canonical label, present a revised checkpoint, and wait again. A model above the role default still requires exact authorization under the Agent-upgrade contract; routing disclosure alone never authorizes it.

Before planning, include the issue table and use the single-step combined repair menu from [multi-issue.md](multi-issue.md) when repair selection is pending. That menu replaces the generic stage-action menu and confirms the selected issue IDs plus entry into stage 3 only; single-step mode still requires a later implementation checkpoint. Before implementation, present the completed task decomposition from `tasks.yaml`—task ID, owner Agent label, exclusive file scope, dependency wave, acceptance conditions, `integration_required`, and `integration_scope`—plus the ordered implementation sequence, affected contracts or data, rollback approach, per-issue checks, and combined regression checks. Expand these details for structural, multi-issue, dependency-ordered, contract-changing, migration, concurrency, lifecycle, state-machine, pooled, or otherwise high-blast-radius repairs.

Planning is stage 3, and the implementation checkpoint follows only once `plan.md` and `tasks.yaml` exist. Gate it by mode:

- `PLANNING_MODE: INLINE` — reuse the diagnostician and its canonical label, but do not bypass a repair-selection or single-step gate. In single-step mode, confirm stage 3 before resuming it; when an automatic run already has a frozen repair set, diagnosis may continue directly into planning. A gate-separated resume gets its own bounded dispatch record and task-state path without creating a distinct planner identity.
- `PLANNING_MODE: DEDICATED` — in single-step mode, planning gets its own checkpoint with its own canonical label before the implementation checkpoint.

Do not dispatch an implementer before `plan.md` and `tasks.yaml` exist, do not duplicate the planning and implementation checkpoints, and do not let the task decomposition silently change the frozen `SELECTED_ISSUES`. When a run switches from `INLINE` to `DEDICATED` mid-stage, disclose the new planner label and present the revised checkpoint before dispatching it.

If the implementation proposes an upgrade that lacks exact prior authorization while repair selection is pending, resolve the repair set first using its numbered menu as a scope decision only. Then show a revised implementation checkpoint with the Agent-upgrade menu; options `1` or `2` authorize the displayed implementation transition. Do not write source between those prompts. If the repair set was already selected and no unapproved upgrade is proposed, use the generic stage-action menu below.

For a checkpoint not governed by the combined repair menu or Agent-upgrade menu, offer these actions as its only numbered list and wait:

1. **确认** — execute exactly the proposed phase or Agent batch;
2. **修改/补充/自定义** — incorporate the user's changes or constraints, present the revised checkpoint, and wait again;
3. **暂停流程** — record the last completed phase and exact pending action, then preserve the run as resumable.
4. **取消并结束** — stop the run, preserve all existing work and artifacts, and emit the exit summary.

Confirmation authorizes only the checkpoint just shown. It does not authorize later phases or materially broader actions.

If any non-implementation phase proposes an upgrade that lacks exact prior authorization, use the Agent-upgrade menu instead of the generic stage-action menu. In single-step mode, upgrade options `1` and `2` also authorize the displayed phase or batch, preventing a duplicate confirmation. The modification, pause, and exit choices authorize no phase execution.

Do not ask separately for each member of a safe parallel, read-only Agent batch. Present the batch's roles, purpose, and concurrency once, then use one packaged confirmation.

Write-capable Agents may be packaged only as one implementer wave: every member must come from the approved `tasks.yaml`, own a disjoint `file_scope`, and carry its own canonical label and bounded task; a later wave needs its own confirmation because earlier results may change its scope. Never package two Agents that can write the same file. The integrator is always dispatched alone after all implementers stop, and may write only the displayed `integration_scope` while integration runs.

Within a confirmed phase, routine read-only tool calls and the stated in-scope commands do not require repeated conversational confirmation. Ask again if the phase's scope, permissions, affected files, model routing, or risk materially changes.

## Pause, cancellation, and resume

On pause or cancellation:

- do not start new agents or commands;
- on cancellation, stop active dispatched tasks through the runtime and immediately reclaim terminal workers; pause alone does not authorize a lifecycle stop;
- do not roll back, stash, clean, or discard work unless separately authorized;
- preserve valid artifacts;
- report the current run-control mode, last completed phase, working-tree state, and pending next action.

A pause is resumable and is not a workflow exit. Do not emit `处理总结` while waiting at a phase checkpoint or after the user selects **暂停**. Cancellation or an explicit stop does exit the incident; apply the single exit-summary contract in [workflow.md](workflow.md#completion-summary) immediately before returning control.

On resume, verify that the incident input, artifacts, and working-tree state still match the paused checkpoint. If they changed materially, present a revised checkpoint before continuing.
