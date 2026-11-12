#!/usr/bin/env bash
# Build the ArduCopter SITL binary used by ranger/tests/sitl.
# Ranger-developed file.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
./waf configure --board sitl
./waf copter
ls -l build/sitl/bin/arducopter
