#!/usr/bin/env bash
# Build the RangerH743 bootloader and ArduCopter firmware.
# Ranger-developed file.
#
# Usage: ranger/scripts/build_fw.sh [--skip-baseline] [--rebuild-bootloader]
#
#   --skip-baseline       do not build the upstream reference board first
#   --rebuild-bootloader  recompile Tools/bootloaders/RangerH743_bl.bin.
#                         The bootloader embeds the git hash, so its bytes
#                         change with every commit. By default the committed
#                         binary is used and the working tree stays clean;
#                         CI passes this flag to prove it still compiles.
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
REBUILD_BL=0
for arg in "$@"; do
    case "$arg" in
        --skip-baseline) SKIP_BASELINE=1 ;;
        --rebuild-bootloader) REBUILD_BL=1 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

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

# the main build embeds Tools/bootloaders/<board>_bl.bin
if [ "$REBUILD_BL" = 1 ] || [ ! -f "Tools/bootloaders/${BOARD}_bl.bin" ]; then
    run Tools/scripts/build_bootloaders.py "$BOARD"
else
    echo "using committed Tools/bootloaders/${BOARD}_bl.bin" | tee -a "$LOG"
fi

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
