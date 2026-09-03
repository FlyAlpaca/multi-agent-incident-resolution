# Multi-issue discovery and repair selection

Use this contract whenever investigation can reveal more than one defect, warning, regression, or root-cause candidate. The goal is complete incident triage, not an unbounded repository audit.

## Discover and normalize issues

Do not stop merely because the first root cause is plausible. Search the incident's relevant logs, failing tests, changed paths, runtime evidence, and directly affected callers for additional causally relevant failures.

For each candidate:

- assign a stable ID such as `ISSUE-001`;
- record symptom, trigger, evidence, affected behavior, severity, confidence, and freshness;
- identify whether it is an independent root cause, a duplicate symptom, a downstream effect, or an environmental/pre-existing failure;
- record dependencies and shared-root-cause group when applicable;
- define the smallest acceptance test that would prove it fixed.

Merge duplicate symptoms under one issue. Link downstream effects to their causal issue instead of inflating the count. Keep uncertain candidates visible as `HYPOTHESIS`; do not silently promote them to repairable issues.

Stop discovery at the incident boundary. Do not turn a bug report into a general cleanup, style audit, dependency upgrade, or unrelated vulnerability scan unless the user expands scope.

## Diagnose each issue

Diagnosis must classify every issue as one of:

- `REPAIRABLE`: root cause established, acceptance test defined, and repair is within current authority;
- `NEEDS_DECISION`: evidence is sufficient but the correct behavior, contract, or scope needs user direction;
- `BLOCKED`: required evidence or external state is unavailable;
- `DUPLICATE`: represented by another issue ID;
- `DEFERRED`: intentionally not included in the current repair run;
- `NOT_A_DEFECT`: expected, environmental, or disproved.

For each `REPAIRABLE` issue, record `MINIMAL` or `STRUCTURAL`, confidence, blast radius, dependencies, expected file scope, proposed patch, validation, and `REPAIR_APPROVED: YES | NO`. Shared-root-cause issues may use one repair proposal, but retain per-issue acceptance tests. The file scope lets planning detect overlapping writes before it splits work across implementers.

Before transitioning beyond investigation or diagnosis, apply the reason, scope, and evidence requirements in [the early-exit rules](workflow.md#early-exit-rules). A `NEEDS_DECISION` or `BLOCKED` candidate is not an early-success result; preserve blocked and deferred findings in the ledger and summary.

## Build the repair recommendation

Before any implementation, present a concise issue table in simplified Chinese with:

- issue ID and short title;
- severity and diagnosis confidence;
- root-cause group and dependencies;
- repairability and repair type;
- expected files or subsystem blast radius;
- whether it is included in the recommended set and why.

Do not present a repair menu when there are zero eligible `REPAIRABLE` issues. If the user chooses none, record `SELECTED_ISSUES: NONE` and apply the corresponding early-exit rule; do not create an implementation checkpoint.

Sort by dependency first, then severity and confidence. Show counts for discovered, repairable, recommended, blocked, and deferred issues. If the ledger is long, keep the choice prompt compact but still show every eligible issue ID and link or point to the full ledger; never hide issues from **全部修复**. Make the exact difference between recommended and all eligible sets explicit.

The **recommended repair set** should include:

- the issue that triggered the incident;
- prerequisites required to restore its invariant;
- confirmed related issues whose repair shares the same root cause or patch and adds low marginal risk;
- high-severity confirmed issues within the authorized incident scope when deferral would leave the system unsafe or unreliable.

Exclude speculative, duplicate, unrelated, blocked, or unapproved issues. Exclude a structural or contract-changing issue when it materially expands the request unless the user has approved that expansion.

## Require a repair-set choice

In automatic full-flow mode, present these choices before stage 3:

1. **推荐修复** — implement the explicitly listed recommended issue IDs and explain why this is the preferred risk/value balance.
2. **全部修复** — implement every listed `REPAIRABLE` issue with `REPAIR_APPROVED: YES` that remains inside the current authorization boundary.
3. **更多操作** — open the secondary repair-action menu without selecting a repair set.

If option `3` is selected, present one secondary prompt. With interactive input, supply only options `1` and `2` and use the client-owned **Other** input for customization; with text fallback, also show option `3`:

1. **暂停流程** — preserve the current run as resumable and do not emit the exit summary;
2. **暂不修复并结束** — preserve the diagnosis and issue ledger, make no source changes, exit the incident, and emit the required summary;
3. **其他 / 自定义** — select or exclude issue IDs, change order or approach, add constraints, or request more diagnosis; textual fallback only.

Always keep every skill-supplied repair-choice number visible. Accept either the number or unambiguous text from the user. A client-owned **Other** result at either layer is a custom repair choice. If customization requires selecting from several issue IDs, present the eligible issues in a following numbered choice set while retaining each stable `ISSUE-xxx` ID; use interactive input only when the full set fits its option limit, otherwise use one textual list. Accept numbers, issue IDs, or clear natural-language selections.

Do not interpret **全部修复** as permission to fix hypotheses, blocked issues, unrelated findings, high-impact actions, or issues outside the incident scope. If “all” contains conflicting repairs, structural expansion, or excessive blast radius, identify the conflict and request a narrower decision instead of guessing.

This selection remains a mandatory user decision in automatic mode unless the activating request already says to use the recommended set, all eligible repairs, or an explicit custom issue list.

In single-step mode, include the implementation checkpoint details and present exactly one combined menu for multiple repairable issues:

1. **推荐修复并进入规划与实施** — freeze the listed recommended issue IDs, then run planning and the displayed implementation phase;
2. **全部修复并进入规划与实施** — freeze every listed eligible repairable issue, then run planning and the displayed implementation phase;
3. **更多操作** — open the secondary repair-action menu without authorizing planning or implementation.

Use the same secondary menu defined above. A custom result may select or exclude issue IDs, change constraints, or request more diagnosis; after its details are resolved, present a revised combined checkpoint.

“进入规划与实施” means the run continues into planning and then implementation. Planning is inline in the same diagnostician for a minimal repair and a separate planner Agent for structural or multi-issue work; the checkpoint does not change shape between the two.

This combined menu replaces the generic confirmation menu for that checkpoint. Do not display a second numbered list containing “确认 / 取消 / 修改 / 暂停”. If an upgrade lacks exact prior authorization, this menu selects scope only; follow the two-prompt composition rule in [confirmation.md](confirmation.md), and do not write source until the upgrade menu is resolved.

When only one repairable issue exists in automatic mode, use this compact menu:

1. **修复此问题（推荐）**
2. **更多操作**

Do not show two indistinguishable “recommended” and “all” choices.

For one repairable issue in single-step mode, use:

1. **修复此问题并进入规划与实施（推荐）**
2. **更多操作**

For either single-issue menu, option `2` opens the same secondary menu defined above. This also replaces the generic stage-action menu. Apply the same separate Agent-upgrade prompt rule when an upgrade lacks exact prior authorization.

## Implement and verify the selected set

Freeze the selected issue IDs before writing. A newly discovered issue returns to triage and requires a new selection; do not silently append it.

Decompose the frozen repair set into `plan.md` and `tasks.yaml` during stage 3, before any implementation. The planner maps every selected issue to at least one task, and never merges unrelated issues into one task merely to reduce dispatch count. When two issues must touch the same file, keep them in one task or hand the shared seam to integration; never assign one file to two concurrent implementers.

Dispatch one implementer per task and order repairs by dependency, wave, and shared root cause. Keep unrelated fixes separable when repository policy requires independent commits. If one issue or task fails verification, do not undo verified independent repairs or continue patching it beyond two attempts; mark its status clearly and assess whether dependent tasks must stop.

Apply the bounded recurrence scan defined in [workflow.md](workflow.md#4-verification). For multiple issues, add credible candidates to the ledger and return them to diagnosis and repair selection; never silently append them to `SELECTED_ISSUES` or treat the scan as unrelated cleanup authority.

Verify:

- each task against its own acceptance conditions from `tasks.yaml`;
- each selected issue against its own reproduction or focused test;
- shared-root-cause groups against every linked symptom;
- the selected set with combined integration/regression tests;
- non-selected adjacent issues for accidental behavior changes when their paths overlap.
- removal of temporary diagnostic logging, probes, breakpoints, fixtures, generated data, and configuration overrides unless an item is intentionally part of the approved repair.

Final reporting must list selected-and-fixed, selected-but-blocked/failed, deferred, duplicate, and not-a-defect issue IDs separately.
