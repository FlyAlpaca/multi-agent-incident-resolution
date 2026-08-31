# Entry and stage confirmation

This contract controls user interaction for one incident run. It does not replace or suppress Codex runtime permission, sandbox, or tool approval prompts.

## Numbered choice contract

For every prompt with two or more actions:

1. number skill-supplied choices consecutively from `1`, including structured option labels;
2. keep each number's meaning stable when re-presenting an unresolved prompt;
3. distinguish menu numbers from stable issue IDs such as `ISSUE-003`;
4. show exactly one actionable choice set for the pending decision.

Deliver the complete decision through one surface. Use `request_user_input` when callable and the menu fits its two-or-three-choice limit; otherwise put one numbered list in the final response and end the turn. Never place a pending decision in `commentary`, duplicate it across surfaces, or follow it with an empty final response. Do not assume an IDE or try to change client mode.

When the client adds **Other**, do not add a duplicate custom option; this client-owned label is the only allowed unnumbered action. Text fallback menus may include the defined **其他 / 自定义** choice.

Accept a number, exact label, structured result, or unambiguous natural-language equivalent; multi-select prompts may also use issue IDs. Normalize the choice internally. If input is ambiguous, invalid, or contradictory, take no action and re-display the same menu through the same surface. Custom detail may arrive through **Other** or the following reply and need not be numeric.

## Entry confirmation

This section is the only source of the entry menu for an incident. Render it exactly once for each unresolved entry decision. Do not precede or follow it with another run-control list, a paraphrased copy, or a second set of interactive options.

Before taking workflow actions, present these three choices in simplified Chinese:

1. **自动全流程** — execute the selected `debug`, `diagnose`, `repair`, or `review` scope continuously until completion, a stop condition, an Agent upgrade above the role default, or a high-impact approval boundary; after normal completion, automatically remove only this run's intermediate-artifact directory.
2. **单步确认** — execute one phase or one approved Agent batch at a time and wait for confirmation before the next transition; normal completion also automatically removes only this run's intermediate-artifact directory.
3. **不进入流程** — do not start this workflow. If the user also requested a narrower action that does not rely on the workflow, perform only that action within its existing authorization; otherwise stop.

If the user already says “自动全流程”, “单步确认”, “不进入流程”, or an unambiguous equivalent in the activating request, adopt it without asking again. An explicit `$multi-agent-incident-resolution` invocation selects the skill but does not by itself select run control.

Do not persist the selection globally. Keep it only for the current incident. If the incident materially changes, ask again.

## Automatic full-flow mode

Proceed through the selected workflow scope without routine stage prompts. Still stop for:

- a tool or runtime approval required by the client;
- an action requiring new authority under the skill's high-impact boundary;
- a structural change that materially expands the user's request;
- any workflow stop condition;
- a missing user decision that would materially change the result.

Automatic mode is not blanket authorization for deployment, destructive operations, history rewriting, credential changes, external writes, purchases, or production mutation.

When diagnosis finds repair choices, automatic mode pauses and presents the numbered repair menu defined in [multi-issue.md](multi-issue.md) unless the user preselected a repair set in the activating request. Repair selection is a product/scope decision, not a routine stage prompt.

Both run-control modes pause before every Agent upgrade above the role defaults defined in `SKILL.md`. A general automatic-mode or single-step selection is not approval for a stronger model, higher effort, or higher-compute mode.

Normal completion of either mode includes [run artifact cleanup](workflow.md#run-artifact-cleanup). Entry selection authorizes only deletion of the validated current run directory after scope completion—not shared roots, other runs, source/runtime data, user logs, or artifacts from a non-normal exit.

## Subagent routing disclosure

This contract applies equally to both run-control modes. Automatic execution removes routine phase confirmations, not routing transparency.

As soon as a route is selected, create and retain one canonical label with the dispatch record:

`<角色或稳定标识>（模型：<精确模型>；推理强度：<精确强度>）`

Before dispatching, emit a visible `commentary` update using `下一步执行：<规范披露标签>；任务：<有界职责>`. For a parallel batch, give one concise sentence per subagent with its own canonical label and bounded task. Do not dispatch until every planned subagent has a canonical label and bounded task.

Record the complete dispatch fields required by [artifacts.md](artifacts.md). They include the task plan, expected artifact, activity-channel limits, and task-specific observation schedule; channel limits are not work limits or timeouts.

After dispatch, paste the same canonical label verbatim into every user-facing reference to that specific planned, running, substituted, failed, cancelled, blocked, or completed subagent. Never shorten it to bare wording such as `验证 Agent` or `独立 Reviewer`, even when the route appeared in an earlier update. This applies to progress reports, terminal-result relays, descriptions of a planned next Agent, and the final summary. A substitution creates a new label that must be disclosed before execution; an upgrade still requires the separate confirmation below. Generic descriptions of a workflow stage or role catalog that do not refer to an actual subagent execution are exempt.

Before sending a user-facing message:

1. identify every phrase that refers to an actual past, current, or planned subagent, including a next Agent mentioned only in the final sentence;
2. match each phrase to exactly one retained canonical label and effective route;
3. if any actual subagent reference lacks its full label, or its model/effort differs from the effective dispatch route, do not send the draft—rewrite it first;
4. when several Agents appear in one update, check and label each one separately; an aggregate statement never satisfies another Agent's disclosure.

Invalid: `验证 Agent 正在运行；之后由独立 Reviewer 复核。`

Valid: `验证 Agent（模型：gpt-5.6-luna；推理强度：max）正在运行；之后由独立复核 Agent（模型：gpt-5.6-sol；推理强度：medium）复核。`

## Agent upgrade confirmation

Before every Agent upgrade, show the role, default model/effort, proposed model/effort or compute mode, reason, expected benefit, and additional cost/latency risk. Then present this numbered menu and wait, even when the user requested the upgrade earlier:

1. **确认升级** — authorize only the displayed Agent role and configuration and, in single-step mode, execute the displayed phase or batch;
2. **保持默认** — use the role's default configuration and, in single-step mode, execute the displayed phase or batch if meaningful progress remains possible;
3. **更多操作** — open the secondary action menu without dispatching the Agent.

If option `3` is selected, present one secondary prompt. With interactive input, supply only options `1` and `2` and use the client-owned **Other** input for customization; with text fallback, also show option `3`:

1. **暂停流程** — preserve the current run as resumable and do not emit the exit summary;
2. **结束流程** — exit the incident and emit the required summary;
3. **其他 / 自定义** — choose another model, effort, constraint, or routing approach; textual fallback only.

Keep the same numbers if the answer is ambiguous. A prior exact model-and-effort request may populate the proposed configuration but does not satisfy this prompt. Do not treat a generic preference for quality, automatic execution, or escalation as approval.

## Stage-by-stage confirmation mode

Before each phase transition, Agent switch, or parallel Agent batch, show one concise checkpoint in simplified Chinese containing:

- completed phase and its terminal result;
- proposed next phase;
- whether the next phase is read-only, validates locally, or may write;
- intended files, commands, or mutation scope when known;
- current risks, unresolved assumptions, and relevant stop conditions.

Immediately before the single numbered choice set, describe the next executor in concise prose rather than a table. Apply the shared routing-disclosure contract:

- when the coordinator itself continues without dispatching a subagent, write `下一步执行：当前 Agent，将负责……`; this coordinator identifier is not a subagent route label and does not require hidden session model metadata;
- when delegating one subagent, write `下一步执行：<规范披露标签>；任务：<有界职责>`;
- for a parallel read-only batch, give one short sentence per subagent using the same canonical label and bounded task.

Do not show the confirmation choices or start the phase until every planned subagent has a canonical label, exact model, reasoning effort, and bounded task. If execution changes between the current Agent and a subagent, or any displayed subagent, model, effort, or task changes before execution, create or revise the affected canonical label, present a revised checkpoint, and wait again. A model above the role default still requires the separate Agent-upgrade menu; the routing disclosure describes the plan but never authorizes an upgrade.

Before implementation, include the issue table and use the single-step combined repair menu from [multi-issue.md](multi-issue.md) when repair selection is pending. That menu replaces the generic stage-action menu and confirms both the selected issue IDs and entry into implementation. For a structural, multi-issue, dependency-ordered, contract-changing, migration, concurrency, lifecycle, state-machine, or otherwise high-blast-radius repair, expand this checkpoint with the ordered implementation sequence, dependencies, affected contracts or data, rollback approach, per-issue checks, and combined regression checks. Do not create a separate planning phase or `plan.md` merely to repeat diagnosis and implementation information.

If the implementation proposes an Agent upgrade while repair selection is pending, resolve the repair set first using its numbered menu as a scope decision only. Then show a revised implementation checkpoint with the Agent-upgrade menu; options `1` or `2` authorize the displayed implementation transition. Do not write source between those prompts. If the repair set was already selected and no upgrade is proposed, use the generic stage-action menu below.

For a checkpoint not governed by the combined repair menu or Agent-upgrade menu, offer these actions as its only numbered list and wait:

1. **确认** — execute exactly the proposed phase or Agent batch;
2. **修改/补充** — incorporate the user's changes, present the revised checkpoint, and wait again;
3. **更多操作** — open the secondary action menu without starting the phase.

If option `3` is selected, present one secondary prompt. With interactive input, supply only options `1` and `2` and use the client-owned **Other** input for custom instructions; with text fallback, also show option `3`:

1. **暂停流程** — record the last completed phase and exact pending action, then preserve the run as resumable;
2. **取消并结束** — stop the run, preserve all existing work and artifacts, and emit the exit summary;
3. **其他 / 自定义** — provide another checkpoint action or constraint; textual fallback only.

Confirmation authorizes only the checkpoint just shown. It does not authorize later phases or materially broader actions.

If any non-implementation phase proposes an Agent upgrade, use the Agent-upgrade menu instead of the generic stage-action menu. In single-step mode, upgrade options `1` and `2` also authorize the displayed phase or batch, preventing a duplicate confirmation. Selecting **更多操作** authorizes nothing until its secondary prompt is resolved.

Do not ask separately for each member of a safe parallel, read-only Agent batch. Present the batch's roles, purpose, and concurrency once, then use one packaged confirmation. Never package write-capable Agents together; implementation remains a single-writer phase.

Within a confirmed phase, routine read-only tool calls and the stated in-scope commands do not require repeated conversational confirmation. Ask again if the phase's scope, permissions, affected files, model routing, or risk materially changes.

## Pause, cancellation, and resume

On pause or cancellation:

- do not start new agents or commands;
- do not roll back, stash, clean, or discard work unless separately authorized;
- preserve valid artifacts;
- report the current run-control mode, last completed phase, working-tree state, and pending next action.

A pause is resumable and is not a workflow exit. Do not emit `处理总结` while waiting at a phase checkpoint or after the user selects **暂停**. Cancellation or an explicit stop does exit the incident; apply the single exit-summary contract in [workflow.md](workflow.md#completion-summary) immediately before returning control.

On resume, verify that the incident input, artifacts, and working-tree state still match the paused checkpoint. If they changed materially, present a revised checkpoint before continuing.
