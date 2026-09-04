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

Before rendering any repair menu, resolve the concrete issue-ID set, repair scope, constraints, and authorized next transition for every candidate repair action, then apply the runtime equivalence rule in [confirmation.md](confirmation.md#numbered-choice-contract). If **推荐修复** and **全部修复** resolve to the same eligible issue IDs under the same scope and constraints, merge them into one choice:

- automatic mode: **修复所列问题（推荐）** — list the shared issue IDs and implement that set;
- single-step mode: **修复所列问题并进入规划（推荐）** — list the shared issue IDs, freeze that set, and enter stage 3.

When the shared set contains one issue, the compact labels **修复此问题（推荐）** and **修复此问题并进入规划（推荐）** are equivalent and preferred.

After merging, renumber all remaining actions consecutively. Re-evaluate equivalence whenever diagnosis, eligibility, approval, scope, constraints, or issue membership changes. Compare semantic sets rather than display order or labels; never merge choices whose selected issues, authority, constraints, or next transition differ.

In automatic full-flow mode, present these choices before stage 3:

1. **推荐修复** — implement the explicitly listed recommended issue IDs and explain why this is the preferred risk/value balance.
2. **全部修复** — implement every listed `REPAIRABLE` issue with `REPAIR_APPROVED: YES` that remains inside the current authorization boundary.
3. **修改/补充/自定义** — select or exclude issue IDs, change order or approach, add constraints, or request more diagnosis without selecting a repair set yet.
4. **暂停流程** — preserve the current run as resumable and do not emit the exit summary.
5. **暂不修复并结束** — preserve the diagnosis and issue ledger, make no source changes, exit the incident, and emit the required summary.

Always keep every skill-supplied repair-choice number visible. Accept either the number or unambiguous text from the user. If customization requires selecting from several issue IDs, present every eligible issue in one following numbered choice set while retaining each stable `ISSUE-xxx` ID; do not truncate the list or split it merely because it has many entries. Accept numbers, issue IDs, or clear natural-language selections.

Do not interpret **全部修复** as permission to fix hypotheses, blocked issues, unrelated findings, high-impact actions, or issues outside the incident scope. If “all” contains conflicting repairs, structural expansion, or excessive blast radius, identify the conflict and request a narrower decision instead of guessing.

This selection remains a mandatory user decision in automatic mode unless the activating request already says to use the recommended set, all eligible repairs, or an explicit custom issue list.

In single-step mode, present exactly one combined repair-selection and planning-entry menu for multiple repairable issues:

1. **推荐修复并进入规划** — freeze the listed recommended issue IDs, then run the displayed planning phase;
2. **全部修复并进入规划** — freeze every listed eligible repairable issue, then run the displayed planning phase;
3. **修改/补充/自定义** — select or exclude issue IDs, change constraints, or request more diagnosis without authorizing planning or implementation;
4. **暂停流程** — preserve the current run as resumable and do not emit the exit summary;
5. **暂不修复并结束** — preserve the diagnosis and issue ledger, make no source changes, exit the incident, and emit the required summary.

After a custom choice is resolved, present a revised combined checkpoint.

“进入规划” authorizes stage 3 only. Planning reuses the diagnostician for a minimal repair and uses a separate planner Agent for structural or multi-issue work. After `plan.md` and `tasks.yaml` are complete, present the separate implementation checkpoint required by single-step mode.

This combined menu replaces the generic confirmation menu for that checkpoint. Do not display a second numbered list containing “确认 / 取消 / 修改 / 暂停”. If an upgrade lacks exact prior authorization, this menu selects scope only; follow the two-prompt composition rule in [confirmation.md](confirmation.md), and do not write source until the upgrade menu is resolved.

When only one repairable issue exists in automatic mode, use this compact menu:

1. **修复此问题（推荐）**
2. **修改/补充/自定义** — change the repair approach or constraints, or request more diagnosis.
3. **暂停流程** — preserve the current run as resumable and do not emit the exit summary.
4. **暂不修复并结束** — preserve the diagnosis and issue ledger, make no source changes, exit the incident, and emit the required summary.

The single-issue menu is the one-eligible-issue instance of the same runtime equivalence rule; do not show separate “recommended” and “all” choices that select the same issue.

For one repairable issue in single-step mode, use:

1. **修复此问题并进入规划（推荐）**
2. **修改/补充/自定义** — change the repair approach or constraints, or request more diagnosis without authorizing planning or implementation.
3. **暂停流程** — preserve the current run as resumable and do not emit the exit summary.
4. **暂不修复并结束** — preserve the diagnosis and issue ledger, make no source changes, exit the incident, and emit the required summary.

Either single-issue menu replaces the generic stage-action menu. Apply the same separate Agent-upgrade prompt rule when an upgrade lacks exact prior authorization.

## Implement and verify the selected set

Freeze the selected issue IDs before writing. A newly discovered issue returns to triage and requires a new selection; do not silently append it.

Follow stages 3–6 in [workflow.md](workflow.md) and the [task contract](artifacts.md#task-contract). Map every selected issue to at least one task without merging unrelated issues merely to reduce dispatch count. Keep unrelated fixes separable when repository policy requires independent commits. If one issue or task fails verification, retain verified independent repairs, mark the failure clearly, and assess its dependants.

Apply the bounded recurrence scan defined in [workflow.md](workflow.md#6-verification). For multiple issues, add credible candidates to the ledger and return them to diagnosis and repair selection; never silently append them to `SELECTED_ISSUES` or treat the scan as unrelated cleanup authority.

Verify:

- each task against its own acceptance conditions from `tasks.yaml`;
- each selected issue against its own reproduction or focused test;
- shared-root-cause groups against every linked symptom;
- the selected set with combined integration/regression tests;
- non-selected adjacent issues for accidental behavior changes when their paths overlap.
- removal of temporary diagnostic logging, probes, breakpoints, fixtures, generated data, and configuration overrides unless an item is intentionally part of the approved repair.

Final reporting must list selected-and-fixed, selected-but-blocked/failed, deferred, duplicate, and not-a-defect issue IDs separately.
