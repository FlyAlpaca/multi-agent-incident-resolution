# Artifact contract

Artifacts are concise decision records. Include exact file paths, symbols, commands, and outcomes; omit essays and repeated repository context. Never include credentials or raw secret-bearing output.

Record `RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW`, `RUN_CONTROL: AUTO | STEP`, `ENTRY_SELECTION_INDEX: 1 | 2`, `ARTIFACT_ROOT`, and `RUN_ARTIFACT_DIR` in the first artifact for the incident. Resolve both paths using the discovery contract in [workflow.md](workflow.md#workspace-and-artifact-location). If entry option `3` declines the workflow, do not create an artifact solely to record that choice. When paused, record the last completed phase and exact pending action without marking an unstarted later phase complete.

When a choice affects workflow state, record both its semantic value and the displayed option number after normalizing the user's input. The user may have replied with text; the stored number represents the numbered menu that was shown, not an input-format requirement.

For hierarchical repair menus, `REPAIR_SELECTION_INDEX` records the primary prompt. Selecting **更多操作** leaves `REPAIR_SELECTION: PENDING` and sets `REPAIR_SECONDARY_INDEX: PENDING` until the secondary prompt is resolved. Use `CLIENT_OTHER` when the client-owned free-form option supplies a custom decision without a skill-controlled number; use `NOT_NEEDED` when the primary prompt directly resolves the repair set. The semantic `REPAIR_SELECTION` and `SELECTED_ISSUES` remain authoritative.

Maintain one proposal/dispatch ledger. Give every proposal or dispatch a stable record ID and update that record in place. Include default-route dispatches and upgrades that were defaulted, customized, cancelled, or never dispatched.

Each record contains:

- identity and routing: phase, role, default route, proposed and effective model/effort, canonical disclosure label, and reason;
- assignment: bounded task, high-level steps/milestones, expected result/artifact, and exact activity path;
- channel guards: maximum record count, complete-record bytes, and total file-growth bytes;
- observation plan: initial wait, health-check cadence, no-progress window (maximum 1800 seconds), and credible next milestone;
- decision and outcome: displayed upgrade choice/index when applicable, dispatch status, result status, terminal conclusion or blocker, and `USER_RELAY_STATUS: PENDING | RELAYED | NOT_DISPATCHED`.

Use numeric units for counts, bytes, and durations. The no-progress window must not exceed 1800 seconds (30 minutes) per window; reaching that limit triggers a full health check and checkpoint, not automatic cancellation. Channel guards are not work limits or timeouts; update them prospectively after authorized scope expansion. Preserve old rows without inventing historical values. Reuse the stored disclosure label verbatim. A prior model preference is context, not upgrade approval. Count every above-default proposal in `AGENT_UPGRADE_COUNT`; use `MIXED` when their outcomes differ. Set `RELAYED` only after the terminal result is visible in the main conversation.

Reserve one append-only `<RUN_ARTIFACT_DIR>/.agent-progress/<stable-agent-id>.activity` path per active dispatch. [The workflow protocol](workflow.md#subagent-liveness-and-result-visibility) is authoritative for its schema, validation, reading, lifecycle, and cleanup. The ledger records the path and guards; it does not duplicate the protocol.

All files created by this skill for one run must remain inside that run's recorded `RUN_ARTIFACT_DIR` so normal-completion cleanup can remove the complete intermediate set without scanning or deleting unrelated paths. Do not place workflow caches, test output, draft summaries, or progress state elsewhere. User-supplied incident inputs, project source, runtime data, service logs, and required deliverables are not workflow intermediates and must never be moved into the run directory merely to make cleanup convenient.

Maintain `issue-ledger.md` as the canonical multi-issue inventory. Each row or section must include stable issue ID, title, status, severity, confidence, root-cause group, dependencies, repair type, approval, selection status, and latest verification result. Never renumber an issue during the same incident.

## Resume rules

- `diagnose` may produce or refresh only `evidence.md` and `diagnosis.md`; it must not edit source.
- `repair` requires an existing `diagnosis.md` with `DIAGNOSIS_STATUS: COMPLETE`, a current issue ledger, an explicit non-pending repair selection, and `REPAIR_APPROVED: YES` for every selected issue. The aggregate approval may be `YES` or `PARTIAL`; per-issue approval controls eligibility. If artifacts are absent or stale relative to the incident input or current diff, return to diagnosis and selection.
- `review` can run without prior artifacts against the current diff, source, and tests. Missing artifacts are then a coverage limitation, not an automatic failure.
- A full `debug` run must not reuse artifacts from a different incident or an earlier source state without validating their inputs and Git revision.

## Terminal marker vocabulary

Use applicable markers one per line so humans and simple tooling can verify state:

```text
RUN_MODE: DEBUG | DIAGNOSE | REPAIR | REVIEW
RUN_CONTROL: AUTO | STEP
ENTRY_SELECTION_INDEX: 1 | 2
ARTIFACT_ROOT: <absolute project artifact root or system temporary root>
RUN_ARTIFACT_DIR: <absolute collision-safe directory for this incident>

EVIDENCE_STATUS: COMPLETE | BLOCKED
ISSUE_DISCOVERY_STATUS: COMPLETE | BOUNDED | BLOCKED
ISSUES_FOUND: <non-negative integer>

DIAGNOSIS_STATUS: COMPLETE | BLOCKED
REPAIR_TYPE: MINIMAL | STRUCTURAL | MIXED | UNDETERMINED
CONFIDENCE: HIGH | MEDIUM | LOW | MIXED
REPAIR_APPROVED: YES | PARTIAL | NO

REPAIR_SELECTION: PENDING | RECOMMENDED | ALL | CUSTOM | NONE
REPAIR_SELECTION_INDEX: PENDING | 1 | 2 | 3 | CLIENT_OTHER
REPAIR_SECONDARY_INDEX: NOT_NEEDED | PENDING | 1 | 2 | 3 | CLIENT_OTHER
SELECTED_ISSUES: PENDING | ISSUE-001,ISSUE-002 | NONE

AGENT_UPGRADES: NONE | PENDING | APPROVED | DEFAULTED | CUSTOM | MIXED | CANCELLED
AGENT_UPGRADE_COUNT: <non-negative integer>

IMPLEMENTATION_STATUS: COMPLETE | PARTIAL | BLOCKED
ATTEMPT: 1 | 2

VERIFICATION_STATUS: PASS | PARTIAL | FAIL | BLOCKED
RECURRENCE_SCAN_STATUS: CLEAR | FINDINGS | BLOCKED
RECURRENCE_TRIAGE_STATUS: NOT_NEEDED | PENDING | COMPLETE | BLOCKED
DIAGNOSTIC_RESIDUE_STATUS: CLEAN | RETAINED | BLOCKED

REVIEW_STATUS: COMPLETE
REVIEW_INDEPENDENCE: INDEPENDENT | LIMITED | UNAVAILABLE
DECISION: PASS | FAIL | BLOCKED
```

## Required markers by mode

- `DEBUG` requires run metadata and all investigation, diagnosis, repair-selection, implementation, verification, recurrence, residue, and review markers.
- `DIAGNOSE` requires run metadata plus investigation and diagnosis markers. Record repair selection as `PENDING` or `NONE` when it is discussed, but implementation, verification, and review markers are not required.
- `REPAIR` requires run metadata, a validated diagnosis and repair selection from current artifacts, then implementation, verification, recurrence, residue, and review markers.
- `REVIEW` requires run metadata plus `REVIEW_STATUS`, `REVIEW_INDEPENDENCE`, and `DECISION`. Earlier-phase markers are optional; when absent, state the resulting coverage limitation.
- Agent-upgrade aggregate markers and the dispatch table are required whenever an Agent is proposed or dispatched; otherwise `AGENT_UPGRADES: NONE` and count `0` are sufficient.
- Every dispatched Agent must have a terminal result or an explicit interrupted/unavailable status, a concise conclusion or blocker, and `USER_RELAY_STATUS: RELAYED` before the workflow transitions past that Agent's phase or exits.

Do not claim a later phase passed when an earlier marker required by the current mode is absent, invalid, or contradicted by the artifact body. Standalone `REVIEW` is not blocked solely because investigation, diagnosis, implementation, or verification artifacts are absent.

For a multi-issue run, the diagnosis markers are aggregate summaries: use `MIXED` when repair types or confidence differ, and `PARTIAL` when only some issues are approved. Per-issue values in `issue-ledger.md` control selection and implementation; an aggregate `YES` never overrides a per-issue `NO`.

Use `REPAIR_SELECTION: PENDING` for diagnosis-only output before the user chooses a repair set. Stage 3 cannot begin while selection or selected issues remain `PENDING`. `ISSUE_DISCOVERY_STATUS: BOUNDED` means targeted discovery covered the incident's relevant surfaces and intentionally stopped at the declared scope boundary; it is not a claim that the entire repository is defect-free.

## Evidence quality

Distinguish:

- **fact**: directly observed in source, logs, commands, or tests;
- **inference**: a causal conclusion supported by stated facts;
- **hypothesis**: plausible but not yet confirmed;
- **limitation**: evidence that could not be obtained and why.

When a sandbox or environment may distort networking, process control, timing, permissions, or external services, label the result as environment-specific and follow repository-prescribed checks before declaring the service or credentials invalid.
