#!/bin/sh

set -eu

SCRIPT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
AGENTS_HOME=${AGENTS_HOME:-${HOME}/.agents}
GLOBAL_SKILLS_ROOT=${GLOBAL_SKILLS_ROOT:-${AGENTS_HOME}/skills}
SKILL_NAME=multi-agent-incident-resolution
GLOBAL_SKILL_PATH=${GLOBAL_SKILLS_ROOT}/${SKILL_NAME}

mkdir -p "$GLOBAL_SKILLS_ROOT"

expected=$(readlink -f -- "$SCRIPT_ROOT")
if [ -L "$GLOBAL_SKILL_PATH" ]; then
    actual=$(readlink -f -- "$GLOBAL_SKILL_PATH")
    if [ "$actual" = "$expected" ]; then
        printf 'global_skill=linked path=%s target=%s\n' "$GLOBAL_SKILL_PATH" "$expected"
        exit 0
    fi
    printf '%s\n' "global skill link points elsewhere: ${GLOBAL_SKILL_PATH} -> ${actual}" >&2
    exit 73
fi

if [ -e "$GLOBAL_SKILL_PATH" ]; then
    printf '%s\n' "global skill path already exists and is not the expected symlink: ${GLOBAL_SKILL_PATH}" >&2
    exit 73
fi

ln -s -- "$expected" "$GLOBAL_SKILL_PATH"
printf 'global_skill=linked path=%s target=%s\n' "$GLOBAL_SKILL_PATH" "$expected"
