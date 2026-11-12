#!/usr/bin/env bash
# Build the RangerH743 bootloader and ArduCopter firmware.
# Ranger-developed file. Usage: ranger/scripts/build_fw.sh [--skip-baseline]
#
# Output: artifacts/RangerH743/ (firmware, bootloader, generated hwdef.h,
# DMA allocation, build log, checksums).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BOARD=RangerH743
BASELINE=MatekH743
OUT="$ROOT/artifacts/$BOARD"
SKIP_BASELINE=0
[ "${1:-}" = "--skip-baseline" ] && SKIP_BASELINE=1

mkdir -p "$OUT"
LOG="$OUT/build.log"
: > "$LOG"

run() {
    echo "+ $*" | tee -a "$LOG"
    "$@" 2>&1 | tee -a "$LOG"
}

{
    echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "commit: $(git rev-parse HEAD)"
    echo "describe: $(git describe --tags --always --dirty 2>/dev/null || true)"
    echo "arm-none-eabi-gcc: $(arm-none-eabi-gcc --version | head -1)"
    echo "python: $(python3 --version)"
} | tee -a "$LOG"

if [ "$SKIP_BASELINE" = 0 ]; then
    # an unmodified upstream H743 board proves the toolchain itself works
    run ./waf configure --board "$BASELINE"
    run ./waf copter
fi

# bootloader first: the main build embeds Tools/bootloaders/<board>_bl.bin
run Tools/scripts/build_bootloaders.py "$BOARD"

run ./waf configure --board "$BOARD"
run ./waf copter

B="build/$BOARD"
cp "$B"/bin/arducopter.apj "$B"/bin/arducopter.bin "$OUT"/
[ -f "$B/bin/arducopter.hex" ] && cp "$B/bin/arducopter.hex" "$OUT"/
[ -f "$B/bin/arducopter_with_bl.hex" ] && cp "$B/bin/arducopter_with_bl.hex" "$OUT"/
cp "Tools/bootloaders/${BOARD}_bl.bin" "$OUT"/
[ -f "Tools/bootloaders/${BOARD}_bl.hex" ] && cp "Tools/bootloaders/${BOARD}_bl.hex" "$OUT"/
cp "$B/hwdef.h" "$OUT/hwdef.h"
arm-none-eabi-size "$B/bin/arducopter" | tee "$OUT/size.txt" | tee -a "$LOG"
(cd "$OUT" && sha256sum arducopter* "${BOARD}"_bl.* > SHA256SUMS)

echo "artifacts in $OUT:" | tee -a "$LOG"
ls -l "$OUT" | tee -a "$LOG"
