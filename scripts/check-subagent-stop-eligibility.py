#!/usr/bin/env python3
"""Fail closed unless the expected dispatched subagent may be stopped right now."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ACTIVE_STATUSES = {"PENDING", "RUNNING", "WAITING"}
TERMINAL_STATUSES = {"BLOCKED", "NEED_INPUT", "DONE", "FAILED", "CANCELLED"}
NO_PROGRESS_THRESHOLD = timedelta(minutes=60)
EXCEPTION_EVIDENCE_TYPES = {
    "user-cancellation": "user-message",
    "runtime-safety": "runtime-signal",
    "authority-stop": "authority-boundary",
}
REQUIRED_STATE_FIELDS = {
    "STATE_VERSION",
    "TASK",
    "AGENT",
    "MODEL",
    "HANDOFF_PROTOCOL_STATUS",
    "STATUS",
    "PHASE",
    "GOAL",
    "CHECKPOINT_ID",
    "CURRENT_PROGRESS",
    "NEXT_STEP",
    "BLOCKER",
    "last_meaningful_progress",
    "last_meaningful_progress_reason",
    "NEEDS_COORDINATOR",
    "NEEDS_USER",
}
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def parse_timestamp(value: str, field: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone offset: {value}")
    return parsed


def read_state(path: Path, expected_task_id: str) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read state file {path}: {exc}") from exc

    fields: dict[str, str] = {}
    plan_markers: list[str] = []
    saw_plan = False
    for line in lines:
        stripped = line.strip()
        if stripped == "PLAN:":
            saw_plan = True
        if re.match(r"^\[(?:x|>| )\]\s+\S", stripped):
            plan_markers.append(stripped[1])
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in REQUIRED_STATE_FIELDS:
            if key in fields:
                raise ValueError(f"state file contains duplicate field: {key}")
            fields[key] = value.strip()

    missing = REQUIRED_STATE_FIELDS - fields.keys()
    if missing:
        raise ValueError(f"state file is missing fields: {', '.join(sorted(missing))}")
    if fields["STATE_VERSION"] != "5":
        raise ValueError("stop eligibility requires STATE_VERSION: 5")
    if not all(fields[field] for field in REQUIRED_STATE_FIELDS):
        raise ValueError("state file contains an empty required field")
    task_id = fields["TASK"].split(maxsplit=1)[0]
    if task_id != expected_task_id:
        raise ValueError(
            f"state TASK {task_id!r} does not match expected task {expected_task_id!r}"
        )
    if path.name != "state.md" or path.parent.name != expected_task_id:
        raise ValueError("state path is not tasks/<expected-task-id>/state.md")
    try:
        checkpoint_id = int(fields["CHECKPOINT_ID"])
    except ValueError as exc:
        raise ValueError("CHECKPOINT_ID must be a non-negative integer") from exc
    if checkpoint_id < 0:
        raise ValueError("CHECKPOINT_ID must be a non-negative integer")
    for field in ("NEEDS_COORDINATOR", "NEEDS_USER"):
        if fields[field] not in {"YES", "NO"}:
            raise ValueError(f"{field} must be YES or NO")

    status = fields["STATUS"]
    if status not in ACTIVE_STATUSES | TERMINAL_STATUSES:
        raise ValueError(f"unsupported STATUS: {status}")
    if fields["HANDOFF_PROTOCOL_STATUS"] not in {"VALID", "INVALID"}:
        raise ValueError("HANDOFF_PROTOCOL_STATUS must be VALID or INVALID")
    if status in ACTIVE_STATUSES and fields["HANDOFF_PROTOCOL_STATUS"] != "VALID":
        raise ValueError("an active state requires HANDOFF_PROTOCOL_STATUS: VALID")
    if not saw_plan or not plan_markers:
        raise ValueError("state file must contain a non-empty PLAN")
    current_steps = plan_markers.count(">")
    if status in ACTIVE_STATUSES and current_steps != 1:
        raise ValueError("an active state must contain exactly one current PLAN step")
    if status in TERMINAL_STATUSES and current_steps != 0:
        raise ValueError("a terminal state must not contain a current PLAN step")
    if status in TERMINAL_STATUSES and not path.with_name("result.md").is_file():
        raise ValueError("a terminal state requires sibling result.md")
    return fields


def read_ledger_binding(
    path: Path,
    record_id: str,
    expected_task_id: str,
    expected_agent_id: str,
    expected_state_path: Path,
    allow_missing_task_path: bool = False,
) -> datetime:
    if not TASK_ID_PATTERN.fullmatch(expected_task_id):
        raise ValueError(
            "--expected-task-id must be one path segment containing only letters, "
            "digits, underscores, and hyphens"
        )
    ledger_path = Path(os.path.abspath(path))
    run_dir = ledger_path.parent
    tasks_dir = run_dir / "tasks"
    task_dir = tasks_dir / expected_task_id
    canonical_state_path = task_dir / "state.md"
    if ledger_path.name != "dispatch-ledger.md":
        raise ValueError("--ledger-path must name dispatch-ledger.md")
    if expected_state_path != canonical_state_path:
        raise ValueError(
            "state path must be <dispatch-ledger-directory>/tasks/<task-id>/state.md"
        )
    for label, candidate in (
        ("dispatch ledger", ledger_path),
        ("run directory", run_dir),
        ("tasks directory", tasks_dir),
        ("task directory", task_dir),
        ("state file", canonical_state_path),
    ):
        if candidate.is_symlink():
            raise ValueError(f"{label} must not be a symbolic link")
    if not ledger_path.is_file() or not run_dir.is_dir():
        raise ValueError("dispatch ledger and canonical run directory must exist")
    if allow_missing_task_path:
        if tasks_dir.exists() and not tasks_dir.is_dir():
            raise ValueError("canonical tasks path must be a directory when present")
        if task_dir.exists() and not task_dir.is_dir():
            raise ValueError("canonical task path must be a directory when present")
    elif not tasks_dir.is_dir() or not task_dir.is_dir():
        raise ValueError("canonical tasks and task directories must exist")
    try:
        text = ledger_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read dispatch ledger {path}: {exc}") from exc

    heading_pattern = re.compile(
        rf"^##[ \t]+{re.escape(record_id)}[ \t]*$", flags=re.MULTILINE
    )
    headings = list(heading_pattern.finditer(text))
    if len(headings) != 1:
        raise ValueError(
            f"dispatch ledger must contain exactly one exact heading for {record_id!r}"
        )
    section_start = headings[0].end()
    next_heading = re.search(r"^##[ \t]+\S", text[section_start:], flags=re.MULTILINE)
    section_end = (
        section_start + next_heading.start() if next_heading is not None else len(text)
    )
    section = text[section_start:section_end]

    def unique_value(pattern: str, field: str) -> str:
        values = re.findall(pattern, section, flags=re.MULTILINE)
        if len(values) != 1:
            raise ValueError(f"dispatch record must contain exactly one {field}")
        return values[0].strip()

    task_id = unique_value(r"^\s*TASK_ID:\s*(\S+)\s*$", "TASK_ID")
    agent_id = unique_value(r"^\s*runtime_agent_id:\s*(\S+)\s*$", "runtime_agent_id")
    state_path = unique_value(r"^\s*state_path:\s*(.+?)\s*$", "state_path")
    dispatch_started_at = parse_timestamp(
        unique_value(
            r"^\s*dispatch_started_at:\s*(.+?)\s*$", "dispatch_started_at"
        ),
        "dispatch_started_at",
    )
    if task_id != expected_task_id:
        raise ValueError("dispatch TASK_ID does not match --expected-task-id")
    if agent_id != expected_agent_id:
        raise ValueError("dispatch runtime_agent_id does not match --expected-agent-id")
    if not Path(state_path).is_absolute():
        raise ValueError("dispatch state_path must be absolute")
    if Path(os.path.abspath(state_path)) != expected_state_path:
        raise ValueError("dispatch state_path does not match the supplied state path")
    return dispatch_started_at


def emit(**payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Check the mandatory gate before a subagent lifecycle stop."
    )
    parser.add_argument("state_path", type=Path)
    parser.add_argument("--ledger-path", required=True, type=Path)
    parser.add_argument("--ledger-record", required=True)
    parser.add_argument("--expected-task-id", required=True)
    parser.add_argument("--expected-agent-id", required=True)
    parser.add_argument("--now", help="ISO 8601 observation time; defaults to UTC now")
    parser.add_argument("--exception", choices=sorted(EXCEPTION_EVIDENCE_TYPES))
    parser.add_argument(
        "--evidence-type", choices=sorted(set(EXCEPTION_EVIDENCE_TYPES.values()))
    )
    parser.add_argument("--evidence", help="Auditable artifact/message/signal reference")
    parser.add_argument(
        "--final-assessment-no-useful-path",
        action="store_true",
        help="Confirm the post-threshold assessment found no reasonable or useful path",
    )
    args = parser.parse_args(argv)

    state_path = Path(os.path.abspath(args.state_path))
    try:
        dispatch_started_at = read_ledger_binding(
            args.ledger_path,
            args.ledger_record,
            args.expected_task_id,
            args.expected_agent_id,
            state_path,
            allow_missing_task_path=bool(args.exception),
        )
    except ValueError as exc:
        emit(decision="DENY_INVALID_BINDING", stop_allowed=False, error=str(exc))
        return 2

    identity = {
        "task": args.expected_task_id,
        "runtime_agent_id": args.expected_agent_id,
        "ledger_record": args.ledger_record,
        "dispatch_started_at": dispatch_started_at.isoformat(),
    }
    try:
        state = read_state(state_path, args.expected_task_id)
        state_validation = "VALID"
        state_error = None
    except ValueError as exc:
        state = {}
        state_validation = "UNAVAILABLE_OR_INVALID"
        state_error = str(exc)

    terminal_clock_error = None
    if state.get("STATUS") in TERMINAL_STATUSES:
        try:
            observed_at = (
                parse_timestamp(args.now, "--now")
                if args.now
                else datetime.now(timezone.utc)
            )
            progress_at = parse_timestamp(
                state["last_meaningful_progress"], "last_meaningful_progress"
            )
        except ValueError as exc:
            terminal_clock_error = str(exc)
        else:
            common = {
                **identity,
                "status": state["STATUS"],
                "observed_at": observed_at.isoformat(),
                "last_meaningful_progress": progress_at.isoformat(),
            }
            if progress_at < dispatch_started_at or observed_at < dispatch_started_at:
                terminal_clock_error = (
                    "terminal progress and observation clocks must not precede dispatch"
                )
            else:
                emit(**common, decision="ALLOW_TERMINAL_RECLAIM", stop_allowed=True)
                return 0

    if args.exception:
        expected_evidence_type = EXCEPTION_EVIDENCE_TYPES[args.exception]
        if (
            args.final_assessment_no_useful_path
            or args.evidence_type != expected_evidence_type
            or not (args.evidence or "").strip()
        ):
            emit(
                **identity,
                decision="DENY_INVALID_EXCEPTION_EVIDENCE",
                stop_allowed=False,
                exception=args.exception,
                required_evidence_type=expected_evidence_type,
            )
            return 2
        exception_state_validation = (
            "INVALID_CLOCK" if terminal_clock_error else state_validation
        )
        exception_state_error = terminal_clock_error or state_error
        emit(
            **identity,
            decision="ALLOW_EXCEPTION_STOP",
            stop_allowed=True,
            exception=args.exception,
            evidence_type=args.evidence_type,
            evidence=args.evidence.strip(),
            state_validation=exception_state_validation,
            state_status=state.get("STATUS"),
            state_error=exception_state_error,
        )
        return 0
    if args.evidence_type or args.evidence:
        emit(**identity, decision="DENY_EVIDENCE_WITHOUT_EXCEPTION", stop_allowed=False)
        return 2

    if state_validation != "VALID":
        emit(
            **identity,
            decision="DENY_INVALID_STATE",
            stop_allowed=False,
            error=state_error,
        )
        return 2

    try:
        observed_at = (
            parse_timestamp(args.now, "--now")
            if args.now
            else datetime.now(timezone.utc)
        )
        progress_at = parse_timestamp(
            state["last_meaningful_progress"], "last_meaningful_progress"
        )
    except ValueError as exc:
        emit(**identity, decision="DENY_INVALID_STATE", stop_allowed=False, error=str(exc))
        return 2

    status = state["STATUS"]
    common = {
        **identity,
        "status": status,
        "observed_at": observed_at.isoformat(),
        "last_meaningful_progress": progress_at.isoformat(),
    }

    if progress_at < dispatch_started_at or observed_at < dispatch_started_at:
        emit(**common, decision="DENY_CLOCK_INCONSISTENCY", stop_allowed=False)
        return 2

    elapsed_seconds = (observed_at - progress_at).total_seconds()
    eligible_at = progress_at + NO_PROGRESS_THRESHOLD
    common.update(
        elapsed_without_progress_seconds=elapsed_seconds,
        force_termination_eligible_after=eligible_at.isoformat(),
    )
    if elapsed_seconds < 0:
        emit(**common, decision="DENY_CLOCK_INCONSISTENCY", stop_allowed=False)
        return 2
    if elapsed_seconds <= NO_PROGRESS_THRESHOLD.total_seconds():
        emit(**common, decision="DENY_BEFORE_THRESHOLD", stop_allowed=False)
        return 3
    if not args.final_assessment_no_useful_path:
        emit(**common, decision="REQUIRE_FINAL_ASSESSMENT", stop_allowed=False)
        return 4

    emit(**common, decision="ALLOW_STALLED_ACTIVE_STOP", stop_allowed=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
