# Workflow

Use all applicable stages for `debug`, stages 1-2 for standalone `diagnose`, stages 3-5 for `repair`, and stage 5 for standalone `review`, unless an early-exit rule below applies. At `repair` entry, validate and normalize a supplied diagnosis into the required run artifacts; re-enter stages 1-2 only when it is stale or incomplete, or when later evidence invalidates the repair direction. A standalone `review` remains project-source read-only and never transitions into diagnosis or repair without a new user-authorized scope. Repository-specific instructions override storage locations, commands, and commit policy.

## Early-exit rules

The nominal stage list is an upper bound. After every phase terminal result, apply the first matching rule before starting or dispatching the next phase:

| Condition | `EARLY_EXIT_REASON` | Exit after | Required evidence |
|---|---|---|---|
| Investigation finds no credible defect or actionable incident issue | `NO_ISSUE` | Investigation | Complete or bounded discovery, zero issues, and disproved candidates |
| In `debug` or `repair`, diagnosis leaves no approved actionable repair | `NO_ACTIONABLE_REPAIR` | Diagnosis | Per-issue classifications and reasons, including deferred items |
| In `debug` or `repair`, the user selects no repair | `NO_REPAIR_SELECTED` | Repair selection | Explicit selection and `SELECTED_ISSUES: NONE` |
| An approved repair is already present and focused verification passes without a source change | `CHANGE_ALREADY_PRESENT` | Verification | `IMPLEMENTATION_STATUS: NO_CHANGE` plus focused verification of the original invariant |
| A standalone review has no changed artifact in its explicitly resolved scope | `EMPTY_REVIEW_SCOPE` | Review scope check | The resolved comparison target and evidence that its diff is empty |

`NEEDS_DECISION` and `BLOCKED` are not early-success conditions. An absent implementation diff is also not success while the approved issue remains: record a partial or blocked outcome. A valid early exit produces the artifacts and markers for phases actually run plus one `处理总结`; skipped phases remain unmarked. Full and early completions may clean the current run directory, while partial, failed, blocked, stopped, cancelled, and paused exits retain it.

## Workspace and artifact location

Before creating any workflow artifact, resolve the repository root and automatically discover whether the project already defines a shared intermediate-artifact root. Inspect only cheap, relevant evidence in this precedence order:

1. repository instructions such as `AGENTS.md` and an explicitly documented artifact-path policy;
2. project configuration or quality scripts that route several rebuildable outputs—tests, lint, coverage, build, or diagnostics—under one common root;
3. an existing repository-root `.artifacts/` or `artifacts/` directory that is clearly designated for intermediate outputs and is ignored by version control.

An explicit repository instruction wins. Do not infer a shared root from one tool's private cache, a source/output directory, or runtime locations such as `data/`, `logs/`, `backups/`, database storage, or deployment staging. Resolve relative paths from the repository root, never from an arbitrary process working directory. In a Git workspace, verify the selected in-repository root is ignored or explicitly approved before writing. If equally authoritative candidates conflict, or no safe project root exists, use a unique system temporary directory and disclose that fallback instead of creating a new repository convention.

Place Multi-Agent Incident Resolution records in a collision-safe run directory under the selected root, normally `<artifact-root>/multi-agent-incident-resolution/<YYYY-MM-DD_HH-mm-ss>/`. Derive the base name from the host's configured local wall-clock timezone, not UTC, with `date '+%Y-%m-%d_%H-%M-%S'`, and create the directory atomically. If the base name already exists, append the first available zero-padded decimal discriminator (`-01`, `-02`, ...); never wait for wall-clock time to advance, overwrite, or reuse another run's directory. Reuse the resolved run directory across all phases and delegated Agents. Record both the resolved root and run directory in the first artifact and every Agent handoff.

The current run directory is disposable only under [Run artifact cleanup](#run-artifact-cleanup). Until cleanup begins, treat it as required workflow evidence.

Before delegating, record the incident input and workspace root. Every phase must read the same incident input and applicable repository instructions. Later phases read prior artifact files rather than receiving a rewritten narrative.

Apply the selected run-control mode from [confirmation.md](confirmation.md). In **单步确认** mode, stop before stages 1-5 and before every Agent switch or parallel Agent batch; present the required checkpoint and wait. A phase terminal marker does not authorize the next phase.

## Subagent state, liveness and result visibility

Before dispatching or monitoring a subagent, follow [the subagent state and timeout protocol](subagent-state.md) as the sole authority for task paths, work-step checkpoints, lifecycle state, observation thresholds, lifecycle-stop exceptions, and terminal preservation. Resolve its task paths under the current `<RUN_ARTIFACT_DIR>` and create the dispatch-ledger record required by [artifacts.md](artifacts.md) before dispatch. Pass the state path and checkpoint obligations in the assignment; after dispatch, observe passively and keep coordinator observations in the ledger rather than rewriting a live subagent's state or sending it follow-up messages.

Before changing phase or exiting, complete the result-consumption, runtime-terminal-confirmation, ledger, and visible-relay gates in [subagent-state.md](subagent-state.md#terminal-handling). Apply [the routing-disclosure contract](confirmation.md#subagent-routing-disclosure) to the relay.

## 1. Investigation

Goal: establish reproducible facts without editing source.

Use one primary investigator. Add parallel read-only investigators only when the issue has genuinely independent surfaces, such as logs, code paths, and runtime/environment evidence.

Produce `evidence.md` with:

- expected and observed behavior;
- trigger and reproduction status;
- timestamped evidence and exact commands;
- earliest causally relevant failure;
- relevant code path and invariant candidates;
- facts separated from hypotheses;
- unexplained gaps;
- `EVIDENCE_STATUS: COMPLETE` or `EVIDENCE_STATUS: BLOCKED`.

Do not recommend a patch merely because a log line looks suspicious.

Also maintain `issue-ledger.md` using [multi-issue.md](multi-issue.md). Continue targeted discovery after the first issue only while evidence stays within the incident boundary. Merge duplicate symptoms and record independent candidates instead of forcing all evidence into one root cause.

Before starting diagnosis, apply [Early-exit rules](#early-exit-rules). If no credible issue remains, finalize the investigation artifacts and exit; do not dispatch a diagnostician or proceed because `debug` nominally lists later stages.

## 2. Diagnosis

Use an independent diagnosis agent when available. It must read the incident input and `evidence.md`, inspect relevant source as needed, and make no edits.

Produce `diagnosis.md` with:

- symptom, trigger, contributing factors, root cause, and downstream effect;
- causal chain and violated invariant;
- `REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED | UNDETERMINED`;
- smallest plausible correct patch and blast radius;
- rejected alternatives and why;
- focused and regression acceptance tests;
- `CONFIDENCE: HIGH | MEDIUM | LOW | MIXED`;
- `REPAIR_APPROVED: YES | PARTIAL | NO`;
- `DIAGNOSIS_STATUS: COMPLETE | BLOCKED`.

For multiple issues, these top-level markers may use `REPAIR_TYPE: MIXED`, `CONFIDENCE: MIXED`, and `REPAIR_APPROVED: PARTIAL`; the issue ledger must retain the exact per-issue values that govern repair selection.

Diagnose and classify every issue in `issue-ledger.md`. A full diagnosis may be complete when some issues are explicitly `BLOCKED`, `DEFERRED`, `DUPLICATE`, or `NOT_A_DEFECT`, but each such status needs evidence and a reason.

In `debug` or `repair`, if diagnosis leaves no approved, actionable repair for this run, apply [Early-exit rules](#early-exit-rules) and exit after recording the diagnosis. A standalone `diagnose` instead completes at its normal scope boundary. A repair menu is unnecessary when there are no eligible repairs. If a user explicitly chooses not to repair, record the selection and exit without implementation or review.

Consider expert escalation when confidence is low, minimal versus structural is unresolved, the issue crosses multiple modules, it involves concurrency/state machines/complex data models, or the same repair direction has failed twice. Start from the diagnosis default, `gpt-5.6-sol` with `medium` effort. A stronger model, effort, or compute mode follows the authorization contract in [confirmation.md](confirmation.md), including in automatic mode. The expert returns `PROCEED` or `RETURN_TO_DIAGNOSIS`; it does not edit source. Do not implement while it recommends returning to diagnosis.

## 3. Implementation

Proceed only with `DIAGNOSIS_STATUS: COMPLETE`, a valid per-issue approval, and an explicit repair-set choice under [multi-issue.md](multi-issue.md). Freeze `SELECTED_ISSUES` before writing. Newly discovered issues return to triage and selection rather than silently expanding implementation.

Assign exactly one writer. Give it the incident input, `evidence.md`, `diagnosis.md`, repository instructions, the current working-tree snapshot, and the attempt number.

The writer must:

- preserve unrelated and pre-existing changes;
- implement the smallest change that restores the invariant;
- keep public behavior stable unless the approved diagnosis requires a contract change;
- add or adjust tests to prove behavior, never merely to make assertions pass;
- update required architecture/product documentation in the same change;
- track any temporary logging, probes, breakpoints, fixtures, generated data, or configuration used during repair so verification can prove they were removed or intentionally retained;
- avoid opportunistic cleanup and unrelated formatting;
- follow repository-specific environment and commit rules.

Produce `implementation.md` containing selected issue IDs, per-issue or shared-direction attempt numbers, files changed, behavioral differences, deviations from diagnosis, tests added, and `IMPLEMENTATION_STATUS: COMPLETE | NO_CHANGE | PARTIAL | BLOCKED`.

If the writer finds that the approved repair may already be present, use `IMPLEMENTATION_STATUS: NO_CHANGE` and record why. Proceed to focused verification of the original invariant; only a passing result permits `EARLY_EXIT_REASON: CHANGE_ALREADY_PRESENT`. If the check fails or cannot distinguish the diagnosis from a pre-existing or environmental failure, end partial or blocked rather than treating the absent diff as success. Independent review is unnecessary when the resolved comparison confirms that this run made no source change.

## 4. Verification

Verification is a separate judgment from implementation. It may run in a delegated agent after the writer has stopped editing.

Validate progressively:

1. reproduce the original failure or its focused regression test;
2. run the focused test;
3. run relevant integration tests;
4. run proportionate broader regression, lint, type, or build checks;
5. perform one bounded recurrence scan for the same violated invariant or defect pattern within the incident's affected surface;
6. inspect the final diff and workspace for unintended changes and diagnostic residue.

The recurrence scan is discovery, not blanket repair authority. Record its exact scope and search method. Set `RECURRENCE_SCAN_STATUS: CLEAR` with `RECURRENCE_TRIAGE_STATUS: NOT_NEEDED` when no credible candidate is found. Otherwise set the scan to `FINDINGS` and triage to `PENDING`, add candidates to `issue-ledger.md`, and do not modify them unless the user selects them through the repair menu. Set triage to `COMPLETE` only after every finding is classified, selected, or explicitly deferred. Merge duplicates and downstream symptoms instead of inflating the issue count. Do not expand the scan into a repository-wide cleanup.

Diagnostic residue includes temporary logs, probes, breakpoints, debug-only branches, fixtures, generated data, environment overrides, and configuration changes. Remove disposable residue before completion. If any item is intentionally retained, justify it as part of the approved repair and test it accordingly.

Do not treat a passing unrelated test as proof. Classify failures as repair regression, implementation error, diagnosis error, environment problem, or pre-existing failure.

Produce `verification.md` with per-issue commands and results, shared-root-cause symptom coverage, combined regression results, original reproduction outcome, recurrence-scan scope and findings, recurrence-triage state, diagnostic-residue check, unexplained failures, coverage limits, and `VERIFICATION_STATUS: PASS | PARTIAL | FAIL | BLOCKED`.

On the first failed implementation direction for an issue or shared root-cause group, return to diagnosis before attempt two. After its second failed direction, stop patching that issue and invoke expert escalation; do not start attempt three. Continue an independent selected issue only when the failed issue is not its prerequisite and doing so remains safe.

## 5. Independent review

Use a read-only reviewer that did not implement the patch whenever the client and current Agent ownership make that possible. Prefer a fresh Agent with isolated context; a coordinator that did not write the patch also qualifies. The reviewer reads the incident input, all artifacts, applicable repository instructions, Git diff, changed source, and relevant tests. It must not edit, commit, stash, or reset anything. Record `REVIEW_INDEPENDENCE: INDEPENDENT`.

If no independent reviewer is available, a coordinator that implemented the patch may perform a separate read-only fallback pass only when all of these are true: one selected issue, `MINIMAL`, first implementation attempt, low blast radius, and no security, public-contract, persistence, migration, concurrency, lifecycle, or state-machine impact. Stop editing before the fallback, re-read the stated requirements and final diff, run the same review rubric, record `REVIEW_INDEPENDENCE: LIMITED`, and disclose the limitation. For any other repair, record `REVIEW_INDEPENDENCE: UNAVAILABLE` and `DECISION: BLOCKED`; do not weaken the classification merely to complete the run.

Review adversarially for:

- root-cause validity and repair classification;
- invariant restoration and regression risk;
- public API, persistence, concurrency, and backward-compatibility impact;
- security issues, secret exposure, unsafe shell/process behavior, TLS/auth weakening, and path traversal;
- missing or inadequate tests;
- untriaged recurrence-scan findings or leaked diagnostic residue;
- repository-policy and documentation compliance.

Review the issue ledger as well: confirm discovered issues were not silently dropped, selected IDs match the user's choice, non-selected issues were not modified without authority, and every selected issue has focused plus combined verification.

Rank findings `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`. `CRITICAL` and `HIGH` block completion. `MEDIUM` blocks when it materially affects correctness, reliability, security, compatibility, or maintainability.

Produce `review.md` with findings and terminal markers:

- `REVIEW_STATUS: COMPLETE`
- `REVIEW_INDEPENDENCE: INDEPENDENT | LIMITED | UNAVAILABLE`
- `DECISION: PASS | FAIL | BLOCKED`

For `debug` or `repair`, if review fails and the total implementation-attempt limit is not exhausted, return to diagnosis with the findings. For standalone `review`, report the findings and stop with `DECISION: FAIL` or `BLOCKED`; do not diagnose, edit, or start a repair loop. Completion of an implemented repair requires `DECISION: PASS` and an independence value allowed by the rules above.

## Completion summary

After entry, treat the summary as the incident's single workflow-exit hook. Immediately before the run exits, the user-facing exit response must contain exactly one distinct Markdown section headed exactly `处理总结`. An exit occurs when the selected `debug`, `diagnose`, `repair`, or `review` scope completes, an early-exit rule is satisfied, or when the run ends partial, failed, blocked with no permitted progress, explicitly stopped, or cancelled. This applies in both automatic and single-step modes whether or not any file changed.

Do not emit `处理总结` at entry confirmation, a phase transition checkpoint, a repair-selection or Agent-upgrade menu, a routine progress response, or a resumable pause awaiting the next confirmation. Those are intermediate workflow turns even if the client renders them as a completed assistant response. Emit the section only once, when the overall incident run actually exits. A later resume continues the same unsummarized run; if a paused run is later stopped or cancelled instead, emit the summary at that exit. Entry option **Codex 原生处理** disables this workflow and continues under the default Codex workflow, so it never starts this contract.

The summary must appear in the workflow-exit response itself; an artifact, commentary update, commit message, or earlier phase report does not satisfy the requirement.

Use these visible labels under the section. Write `无` only when absence is confirmed, `未确认` plus the reason when evidence is insufficient, and `不适用` when the field does not apply; never use `无` to hide an unfinished check:

- `运行结果` — mode and exit state: completed (including valid early completion), partial, failed, blocked, stopped, or cancelled; identify the early-exit reason when applicable;
- `发现的问题` — what was observed and the issue IDs or shared root-cause groups it represents; when multiple issues exist, separate fixed, failed/blocked, deferred, duplicate, and not-a-defect IDs;
- `根因` — the confirmed causal chain and violated invariant;
- `修改状态` — exactly `已修改`, `部分修改`, or `未修改`, referring only to changes made by this workflow run; list the principal files or components changed, or state why no modification was made without counting pre-existing user changes;
- `处理方式` — diagnosis or repair actions taken, repair type and meaningful behavioral difference; write `未实施修复` when applicable;
- `验证结果` — focused and regression checks, their outcomes, and the independent-review decision or limitation;
- `子 Agent 结论` — when delegation occurred, identify every dispatched Agent and synthesize its terminal outcome, conclusion, material limitation, and effect on the workflow; in either run-control mode, use every Agent's retained canonical disclosure label and apply the same pre-send gate; otherwise write `不适用`;
- `遗留事项` — unresolved, deferred, blocked, partially verified issues, remaining risks, and the concrete next action;
- `交付状态` — whether required documentation was synchronized and whether a commit was created when either is relevant.
- `中间产物清理` — for a normally completed run in either run-control mode, state `已清理` and the exact removed `RUN_ARTIFACT_DIR`, or `失败` with the retained path and reason; for all other exits, state `已保留` and why, or `不适用` when no run artifacts were created.

For multiple selected issues, group details by issue ID when their outcomes differ; do not hide a failed issue behind an aggregate success statement. Do not claim success from an attempted edit alone: clearly distinguish fixed, partially fixed, unverified, and unresolved issues. Synthesize the final artifacts instead of copying their full contents or repeating earlier progress updates.

### Run artifact cleanup

Cleanup is part of a normal or early `RUN_CONTROL: AUTO` or `RUN_CONTROL: STEP` completion, after every required result has been consumed and the complete `处理总结` has been synthesized in memory, but before sending the workflow-exit response. It does not run for partial, failed, blocked, stopped, cancelled, or paused exits. If no run artifacts were created, report cleanup as not applicable.

Invoke `scripts/cleanup-run-artifacts.sh` with the explicit recorded `ARTIFACT_ROOT` and `RUN_ARTIFACT_DIR`. The script must validate that both paths are absolute existing directories, neither target is a symbolic link or broad root, and the run directory is exactly one direct child of `<ARTIFACT_ROOT>/multi-agent-incident-resolution/`. Never replace these arguments with a glob, unresolved environment variable, current directory, workspace root, shared namespace directory, or inferred path. The script removes the current run directory and prunes the skill namespace directory only when it becomes empty; it never removes `ARTIFACT_ROOT`.

After cleanup, perform a read-only existence check of the exact run directory. Report `中间产物清理: 已清理（<RUN_ARTIFACT_DIR>）` only when it is absent. If validation or deletion fails, do not broaden the target or retry with a less restrictive command; report `中间产物清理: 失败` with the retained exact path and concise reason. Cleanup failure changes the completed run's exit state to partial because the user-requested lifecycle is incomplete, while preserving all repair and verification conclusions already synthesized.

## Git checkpoint policy

Git history is evidence, not a disposable checkpoint mechanism.

- Record status and diff before edits and after each phase that mutates files.
- Do not auto-stash user work. If an explicitly authorized operation needs a clean tree, preserve the exact changes in a named stash or patch and report how to recover them.
- Prefer additive revert commits over history rewriting unless the user explicitly requests rewritten history.
- Commit only when the user requested it or repository instructions require it. Keep unrelated changes and independent todo items in separate commits.
