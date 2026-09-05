#!/usr/bin/env python3
"""Behavioral checks for the subagent stop-eligibility gate."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("check-subagent-stop-eligibility.py")
AGENT_ID = "01a06f76-b59a-7192-a7d6-ca9db23fdeff"
PROGRESS = "2026-09-05T10:48:36+08:00"


def require(condition: bool, detail: object) -> None:
    if not condition:
        raise RuntimeError(f"behavioral check failed: {detail}")


def run_case(
    status: str,
    now: str,
    *extra: str,
    task_id: str = "PLAN-001",
    expected_task_id: str = "PLAN-001",
    expected_agent_id: str = AGENT_ID,
    ledger_heading: str = "DISPATCH-PLAN-001",
    dispatch_started_at: str = "2026-09-05T10:48:30+08:00",
    handoff_status: str = "VALID",
    progress: str = PROGRESS,
    complete_schema: bool = True,
    write_state: bool = True,
    create_task_dir: bool = True,
    task_dir_symlink: bool = False,
    state_file_symlink: bool = False,
) -> tuple[int, dict[str, object]]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        tasks_dir = root / "tasks"
        if create_task_dir:
            tasks_dir.mkdir()
        task_dir = tasks_dir / task_id
        if task_dir_symlink:
            outside_task_dir = root / "outside" / task_id
            outside_task_dir.mkdir(parents=True)
            task_dir.symlink_to(outside_task_dir, target_is_directory=True)
        elif create_task_dir:
            task_dir.mkdir(parents=True, exist_ok=True)
        state = task_dir / "state.md"
        if write_state and complete_schema:
            marker = "[>]" if status in {"PENDING", "RUNNING", "WAITING"} else "[x]"
            state.write_text(
                "STATE_VERSION: 5\n"
                f"TASK: {task_id} regression case\n"
                "AGENT: test Agent\n"
                "MODEL: test/model\n"
                f"HANDOFF_PROTOCOL_STATUS: {handoff_status}\n"
                f"STATUS: {status}\n"
                "PHASE: PLANNING\n"
                "GOAL: validate stop gate\n"
                "CHECKPOINT_ID: 1\n\n"
                "PLAN:\n"
                f"{marker} validate stop gate\n\n"
                "CURRENT_PROGRESS: bounded test state\n"
                "NEXT_STEP: none\n"
                "BLOCKER: none\n"
                f"last_meaningful_progress: {progress}\n"
                "last_meaningful_progress_reason: test fixture\n"
                "NEEDS_COORDINATOR: NO\n"
                "NEEDS_USER: NO\n",
                encoding="utf-8",
            )
        elif write_state:
            state.write_text(
                f"TASK: {task_id} regression case\n"
                f"STATUS: {status}\n"
                f"last_meaningful_progress: {progress}\n",
                encoding="utf-8",
            )
        if write_state and state_file_symlink:
            outside_state = root / "outside-state.md"
            outside_state.write_text(state.read_text(encoding="utf-8"), encoding="utf-8")
            state.unlink()
            state.symlink_to(outside_state)
        if write_state and status in {"BLOCKED", "NEED_INPUT", "DONE", "FAILED", "CANCELLED"}:
            (task_dir / "result.md").write_text("terminal result\n", encoding="utf-8")
        ledger = root / "dispatch-ledger.md"
        ledger.write_text(
            f"## {ledger_heading}\n\n"
            f"runtime_agent_id: {AGENT_ID}\n"
            "observation:\n"
            f"  dispatch_started_at: {dispatch_started_at}\n"
            "workflow_metadata:\n"
            f"  TASK_ID: {task_id}\n"
            "assignment:\n"
            f"  state_path: {state}\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(state),
                "--ledger-path",
                str(ledger),
                "--ledger-record",
                "DISPATCH-PLAN-001",
                "--expected-task-id",
                expected_task_id,
                "--expected-agent-id",
                expected_agent_id,
                "--now",
                now,
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    return result.returncode, json.loads(result.stdout)


def check_case(
    expected_code: int,
    expected_decision: str,
    status: str,
    now: str,
    *extra: str,
    **kwargs: object,
) -> None:
    code, payload = run_case(status, now, *extra, **kwargs)
    require(code == expected_code, (code, payload))
    require(payload["decision"] == expected_decision, payload)
    require(payload["stop_allowed"] is (expected_code == 0), payload)


def main() -> int:
    for status in ("PENDING", "RUNNING", "WAITING"):
        check_case(3, "DENY_BEFORE_THRESHOLD", status, "2026-09-05T11:06:11+08:00")
    check_case(3, "DENY_BEFORE_THRESHOLD", "RUNNING", "2026-09-05T11:48:36+08:00")
    check_case(4, "REQUIRE_FINAL_ASSESSMENT", "RUNNING", "2026-09-05T11:48:37+08:00")
    check_case(
        0,
        "ALLOW_STALLED_ACTIVE_STOP",
        "RUNNING",
        "2026-09-05T11:48:37+08:00",
        "--final-assessment-no-useful-path",
    )
    check_case(0, "ALLOW_TERMINAL_RECLAIM", "DONE", "2026-09-05T10:49:00+08:00")
    check_case(
        0,
        "ALLOW_TERMINAL_RECLAIM",
        "DONE",
        "2026-09-05T10:49:00+08:00",
        "--exception",
        "user-cancellation",
        "--evidence-type",
        "user-message",
        "--evidence",
        "conversation cancellation raced with terminal handoff",
    )
    check_case(
        2,
        "DENY_INVALID_STATE",
        "DONE",
        "2026-09-05T10:49:00+08:00",
        handoff_status="GARBAGE",
    )
    check_case(
        2,
        "DENY_CLOCK_INCONSISTENCY",
        "DONE",
        "2026-09-05T12:00:00+08:00",
        progress="2026-09-05T09:00:00+08:00",
    )
    check_case(
        2,
        "DENY_CLOCK_INCONSISTENCY",
        "DONE",
        "2026-09-05T10:00:00+08:00",
        dispatch_started_at="2026-09-05T11:00:00+08:00",
    )
    for now, progress in (
        ("2026-09-05T12:00:00+08:00", "2026-09-05T09:00:00+08:00"),
        ("2026-09-05T10:00:00+08:00", PROGRESS),
    ):
        code, payload = run_case(
            "DONE",
            now,
            "--exception",
            "user-cancellation",
            "--evidence-type",
            "user-message",
            "--evidence",
            "cancellation with a stale terminal snapshot",
            dispatch_started_at="2026-09-05T11:00:00+08:00",
            progress=progress,
        )
        require(code == 0, (code, payload))
        require(payload["decision"] == "ALLOW_EXCEPTION_STOP", payload)
        require(payload["state_validation"] == "INVALID_CLOCK", payload)
    check_case(
        0,
        "ALLOW_EXCEPTION_STOP",
        "RUNNING",
        "2026-09-05T10:49:00+08:00",
        "--exception",
        "user-cancellation",
        "--evidence-type",
        "user-message",
        "--evidence",
        "conversation item msg-123 cancels PLAN-001",
    )
    check_case(
        2,
        "DENY_INVALID_EXCEPTION_EVIDENCE",
        "RUNNING",
        "2026-09-05T10:49:00+08:00",
        "--exception",
        "authority-stop",
        "--evidence-type",
        "user-message",
        "--evidence",
        "wrong evidence type",
    )
    for exception, evidence_type in (
        ("runtime-safety", "runtime-signal"),
        ("authority-stop", "authority-boundary"),
    ):
        check_case(
            0,
            "ALLOW_EXCEPTION_STOP",
            "RUNNING",
            "2026-09-05T10:49:00+08:00",
            "--exception",
            exception,
            "--evidence-type",
            evidence_type,
            "--evidence",
            f"artifact reference for {exception}",
        )
    check_case(
        2,
        "DENY_INVALID_EXCEPTION_EVIDENCE",
        "RUNNING",
        "2026-09-05T10:49:00+08:00",
        "--exception",
        "runtime-safety",
    )
    check_case(
        2,
        "DENY_CLOCK_INCONSISTENCY",
        "RUNNING",
        "2026-09-05T10:48:35+08:00",
    )
    check_case(
        2,
        "DENY_CLOCK_INCONSISTENCY",
        "RUNNING",
        "2026-09-05T12:00:00+08:00",
        progress="2026-09-05T09:00:00+08:00",
    )
    check_case(
        2,
        "DENY_INVALID_STATE",
        "RUNNING",
        "2026-09-05T11:06:11+08:00",
        complete_schema=False,
    )
    check_case(
        2,
        "DENY_INVALID_BINDING",
        "RUNNING",
        "2026-09-05T11:06:11+08:00",
        expected_task_id="PLAN-OTHER",
    )
    check_case(
        2,
        "DENY_INVALID_BINDING",
        "RUNNING",
        "2026-09-05T11:06:11+08:00",
        expected_agent_id="different-runtime-agent",
    )
    check_case(
        2,
        "DENY_INVALID_BINDING",
        "RUNNING",
        "2026-09-05T11:06:11+08:00",
        ledger_heading="DISPATCH-PLAN-001-ARCHIVE",
    )
    for exception, evidence_type, write_state in (
        ("user-cancellation", "user-message", False),
        ("runtime-safety", "runtime-signal", True),
        ("authority-stop", "authority-boundary", True),
    ):
        check_case(
            0,
            "ALLOW_EXCEPTION_STOP",
            "RUNNING",
            "2026-09-05T10:49:00+08:00",
            "--exception",
            exception,
            "--evidence-type",
            evidence_type,
            "--evidence",
            f"auditable reference for {exception}",
            write_state=write_state,
            complete_schema=False,
        )
    check_case(
        0,
        "ALLOW_EXCEPTION_STOP",
        "RUNNING",
        "2026-09-05T10:49:00+08:00",
        "--exception",
        "user-cancellation",
        "--evidence-type",
        "user-message",
        "--evidence",
        "cancellation before task directory bootstrap",
        write_state=False,
        create_task_dir=False,
    )
    check_case(
        2,
        "DENY_INVALID_BINDING",
        "RUNNING",
        "2026-09-05T10:49:00+08:00",
        write_state=False,
        create_task_dir=False,
    )
    for unsafe_task_id in ("../VICTIM", "PLAN/001", ".", "PLAN\\001"):
        check_case(
            2,
            "DENY_INVALID_BINDING",
            "RUNNING",
            "2026-09-05T10:49:00+08:00",
            "--exception",
            "user-cancellation",
            "--evidence-type",
            "user-message",
            "--evidence",
            "auditable cancellation reference",
            task_id=unsafe_task_id,
            expected_task_id=unsafe_task_id,
            write_state=False,
        )
    for symlink_case in ("task-dir", "state-file"):
        check_case(
            2,
            "DENY_INVALID_BINDING",
            "RUNNING",
            "2026-09-05T11:48:37+08:00",
            "--final-assessment-no-useful-path",
            task_dir_symlink=symlink_case == "task-dir",
            state_file_symlink=symlink_case == "state-file",
        )
    check_case(
        2,
        "DENY_INVALID_BINDING",
        "RUNNING",
        "2026-09-05T10:49:00+08:00",
        "--exception",
        "user-cancellation",
        "--evidence-type",
        "user-message",
        "--evidence",
        "cancellation cannot bind through a task-directory symlink",
        write_state=False,
        task_dir_symlink=True,
    )
    print("subagent-stop-eligibility: valid cases=36")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
