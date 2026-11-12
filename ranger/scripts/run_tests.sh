#!/usr/bin/env bash
# Run the Ranger test tiers. Ranger-developed file.
#
#   board  static checks of hwdef.dat against the pin map (no build)
#   build  checks of the generated RangerH743 build outputs (needs build_fw.sh)
#   sitl   simulated flight tests (needs build_sitl.sh)
#
# Usage: ranger/scripts/run_tests.sh [board] [build] [sitl]   (default: all)
#
# None of these tiers touches hardware. The hardware bring-up checklist
# is ranger/docs/HARDWARE_BRINGUP.md.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

tiers=("$@")
[ ${#tiers[@]} -eq 0 ] && tiers=(board build sitl)

mkdir -p artifacts/test-results
for t in "${tiers[@]}"; do
    case "$t" in
        board|build)
            python3 -m pytest -v "ranger/tests/$t" \
                --junitxml="artifacts/test-results/$t.xml" ;;
        sitl)
            RANGER_SITL_ARTIFACTS="$ROOT/artifacts/sitl" \
                python3 -m pytest -v ranger/tests/sitl \
                --junitxml=artifacts/test-results/sitl.xml ;;
        *) echo "unknown tier: $t" >&2; exit 2 ;;
    esac
done
