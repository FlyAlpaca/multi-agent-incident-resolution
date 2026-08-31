#!/bin/sh

set -eu

if [ "$#" -ne 2 ]; then
    printf '%s\n' 'usage: cleanup-run-artifacts.sh <artifact-root> <run-artifact-dir>' >&2
    exit 64
fi

artifact_root_input=$1
run_dir_input=$2

case "$artifact_root_input" in
    /*) ;;
    *) printf '%s\n' 'artifact root must be an absolute path' >&2; exit 64 ;;
esac

case "$run_dir_input" in
    /*) ;;
    *) printf '%s\n' 'run artifact directory must be an absolute path' >&2; exit 64 ;;
esac

if [ -L "$artifact_root_input" ] || [ -L "$run_dir_input" ]; then
    printf '%s\n' 'refusing to clean through a symbolic link' >&2
    exit 73
fi

if [ ! -d "$artifact_root_input" ] || [ ! -d "$run_dir_input" ]; then
    printf '%s\n' 'artifact root and run artifact directory must both exist' >&2
    exit 66
fi

artifact_root=$(realpath -e -- "$artifact_root_input")
run_dir=$(realpath -e -- "$run_dir_input")

if [ "$artifact_root" = "/" ] || [ "$run_dir" = "$artifact_root" ]; then
    printf '%s\n' 'refusing to clean a broad artifact target' >&2
    exit 73
fi

run_parent=${artifact_root}/multi-agent-incident-resolution
case "$run_dir" in
    "$run_parent"/*) ;;
    *) printf '%s\n' 'run artifact directory is outside the skill namespace' >&2; exit 73 ;;
esac

run_id=${run_dir#"$run_parent"/}
case "$run_id" in
    ''|.|..|*/*) printf '%s\n' 'run artifact directory must be one direct run-id child' >&2; exit 73 ;;
esac

rm -rf -- "$run_dir"

namespace_pruned=no
if rmdir -- "$run_parent" 2>/dev/null; then
    namespace_pruned=yes
fi

printf 'cleanup_status=complete removed=%s namespace_pruned=%s\n' "$run_dir" "$namespace_pruned"
