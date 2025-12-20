#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/run_scheduled_jobs.sh envs/schedules/5am
#   ./scripts/run_scheduled_jobs.sh envs/schedules/5am --default-jobs sample_orders
#
# Iterates over every .env-style file in the provided schedule directory, loads
# the base client env (if specified), and runs runner.py for the JOBS defined.
# If JOBS is empty, falls back to the provided --default-jobs list.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <schedule-env-directory> [--default-jobs job_a job_b ...]" >&2
  exit 1
fi

ENV_DIR="$1"
shift

DEFAULT_JOBS=()
if [[ $# -gt 0 ]]; then
  if [[ "$1" == "--default-jobs" ]]; then
    shift
    DEFAULT_JOBS=("$@")
  else
    echo "Unknown arguments: $*" >&2
    exit 1
  fi
fi

env_path="$REPO_DIR/$ENV_DIR"
if [[ ! -d "$env_path" ]]; then
  echo "Environment directory not found: $env_path" >&2
  exit 1
fi

ENV_ROOT="$REPO_DIR/envs"

find "$env_path" -type f -name "*.env" -print0 | sort -z | while IFS= read -r -d '' env_file; do
  (
    echo "Running jobs for schedule env $(basename "$env_file")"
    unset BASE_ENV
    unset JOBS
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    if [[ -n "${BASE_ENV:-}" ]]; then
      base_env_path="$ENV_ROOT/$BASE_ENV"
      if [[ ! -f "$base_env_path" ]]; then
        echo "Base env not found for $(basename "$env_file"): $base_env_path" >&2
        exit 1
      fi
      # shellcheck disable=SC1090
      source "$base_env_path"
      # Re-apply schedule overrides after loading base vars
      # shellcheck disable=SC1090
      source "$env_file"
    fi
    set +a

    job_args=()
    if [[ -n "${JOBS:-}" ]]; then
      read -r -a job_array <<<"$JOBS"
      if [[ "${#job_array[@]}" -gt 0 ]]; then
        job_args=(--only "${job_array[@]}")
      fi
    elif [[ "${#DEFAULT_JOBS[@]}" -gt 0 ]]; then
      job_args=(--only "${DEFAULT_JOBS[@]}")
    fi

    cd "$REPO_DIR"
    python runner.py "${job_args[@]}"
  )
done
