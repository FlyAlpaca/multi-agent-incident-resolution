#!/usr/bin/env python3
"""Validate the prompt-test corpus using only the Python standard library."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = {"id", "prompt", "expected"}


def fail(message: str) -> int:
    print(f"test-prompts: invalid: {message}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <test-prompts.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        with path.open(encoding="utf-8") as stream:
            cases = json.load(stream)
    except OSError as exc:
        return fail(f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        return fail(f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")

    if not isinstance(cases, list) or not cases:
        return fail("root must be a non-empty array")

    seen_ids: set[int] = set()
    for position, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            return fail(f"case {position} must be an object")

        missing = REQUIRED_FIELDS - case.keys()
        unexpected = set(case) - REQUIRED_FIELDS
        if missing:
            return fail(f"case {position} is missing fields: {', '.join(sorted(missing))}")
        if unexpected:
            return fail(
                f"case {position} has unexpected fields: {', '.join(sorted(unexpected))}"
            )

        case_id = case["id"]
        if isinstance(case_id, bool) or not isinstance(case_id, int) or case_id <= 0:
            return fail(f"case {position} id must be a positive integer")
        if case_id in seen_ids:
            return fail(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)

        for field in ("prompt", "expected"):
            value = case[field]
            if not isinstance(value, str) or not value.strip():
                return fail(f"case {case_id} {field} must be a non-empty string")

    print(f"test-prompts: valid cases={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
