#!/usr/bin/env bash
#
# Runs the SchoolMint pipeline container for a given school year.
# Usage: run_schoolmint.sh <school-year> [--dbt-refresh]
# Examples:
#   run_schoolmint.sh 2028
#   run_schoolmint.sh 2028 --dbt-refresh

set -euo pipefail

KEY_DIR="/home/data_admin/keys"
LOCK_FILE="/tmp/run_schoolmint.lock"
IMAGE="schoolmint"

usage() {
    echo "Usage: $0 <school-year> [--dbt-refresh]" >&2
    exit 1
}

# --- Parse arguments ---
SCHOOL_YEAR=""
EXTRA_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --dbt-refresh)
            EXTRA_ARGS+=("--dbt-refresh")
            ;;
        -*)
            echo "Error: unknown option '$arg'" >&2
            usage
            ;;
        *)
            if [[ -n "$SCHOOL_YEAR" ]]; then
                echo "Error: more than one school year given" >&2
                usage
            fi
            SCHOOL_YEAR="$arg"
            ;;
    esac
done

if [[ -z "$SCHOOL_YEAR" ]]; then
    usage
fi

if [[ ! "$SCHOOL_YEAR" =~ ^[0-9]{4}$ ]]; then
    echo "Error: school year must be a 4-digit year (got '$SCHOOL_YEAR')" >&2
    exit 1
fi

# --- Prevent overlapping runs ---
exec 9> "$LOCK_FILE"
if ! flock -n 9; then
    echo "Another run is still in progress; skipping." >&2
    exit 0
fi

/usr/bin/docker run --rm \
    -v "$KEY_DIR/schoolmint_pipeline:/root/.ssh/schoolmint_pipeline:ro" \
    -v "$KEY_DIR/known_hosts:/root/.ssh/known_hosts:ro" \
    "$IMAGE" --school-year "$SCHOOL_YEAR" "${EXTRA_ARGS[@]}"
