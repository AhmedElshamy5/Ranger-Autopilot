# Ranger-Autopilot

Firmware for the Ranger UAV custom flight controller (Ranger FC A0.1,
STM32H743VIT6), built on ArduPilot.

> **The Ranger FC has not been manufactured.** This repository contains
> firmware that compiles for the board and passes simulation tests. It
> has never run on Ranger hardware and is not flight-ready.

## What is ArduPilot and what is Ranger

This repository is a fork of [ArduPilot](https://github.com/ArduPilot/ardupilot)
and is licensed under the GPLv3 like ArduPilot (see `COPYING.txt`). The
flight code, RTOS integration, sensor drivers, bootloader, build system
and simulator are ArduPilot's work and are unmodified.

| | |
|---|---|
| Upstream | `https://github.com/ArduPilot/ardupilot` (git remote `upstream`) |
| Baseline | tag `Copter-4.7.2`, commit `fb773567896014da007bca58358704d4a0d8516f` |
| Ranger branch | `ranger/h743-board-port` |

Ranger-developed files, all added by commits on the Ranger branch:

| Path | Content |
|---|---|
| `libraries/AP_HAL_ChibiOS/hwdef/RangerH743/` | Board definition, bootloader definition, default parameters, board README |
| `Tools/bootloaders/RangerH743_bl.bin`, `.hex` | ArduPilot bootloader compiled for RangerH743 |
| `ranger/` | Hardware handoff snapshot, pin map, tests, scripts, docs |
| `.github/workflows/ranger_h743.yml` | CI workflow |
| `RANGER.md` | This file |

Two upstream files are modified: `Tools/AP_Bootloader/board_types.txt`
gains one entry for the fork-local board ID, and `.gitignore` gains the
`artifacts/` output directory.

`git diff Copter-4.7.2..ranger/h743-board-port --stat` lists exactly
what Ranger changed.

## Build

Environment: Ubuntu 22.04 (native or WSL2), set up once with ArduPilot's
own installer, which pins the compiler (`gcc-arm-none-eabi-10-2020-q4-major`):

```
git submodule update --init --recursive
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile
```

Then:

```
ranger/scripts/build_fw.sh      # baseline board, then RangerH743 firmware
ranger/scripts/build_sitl.sh    # simulator binary
ranger/scripts/run_tests.sh     # all test tiers
```

Firmware lands in `artifacts/RangerH743/`:

| File | Use |
|---|---|
| `arducopter_with_bl.hex` | Bootloader + firmware, for SWD programming of a blank board |
| `arducopter.apj` | Firmware for upload through the ArduPilot bootloader |
| `arducopter.bin` | Raw firmware image (loads at `0x08020000`) |
| `RangerH743_bl.bin` | Bootloader alone (loads at `0x08000000`) |
| `hwdef.h` | Generated board configuration, including the DMA allocation |
| `build.log`, `SHA256SUMS`, `size.txt` | Build record |

CI uses ArduPilot's pinned container images
(`ardupilot/ardupilot-dev-chibios:v0.1.3`), the same ones upstream CI
uses.

## Tests

| Tier | Command | Needs | What a pass means |
|---|---|---|---|
| Board | `run_tests.sh board` | nothing | `hwdef.dat` matches the hardware handoff CSVs and the STM32H743 alternate-function table; provisional decisions are still provisional |
| Outputs | `run_tests.sh outputs` | `build_fw.sh` | The firmware was compiled with the intended clock, DMA, sensor and battery configuration, and the images fit the flash layout |
| SITL | `run_tests.sh sitl` | `build_sitl.sh` | MAVLink, parameters, the Ranger failsafe and logging defaults, arming checks, the GCS failsafe, a guided flight, a battery failsafe landing and the flight log work in simulation |
| Hardware | `ranger/docs/HARDWARE_BRINGUP.md` | a board | Not done. Nothing above substitutes for it |

SITL runs ArduPilot's flight code against simulated sensors on a
generic quadcopter model. It does not execute the RangerH743 pin
configuration or drivers, so it says nothing about the Ranger PCB.

## Documentation

- Board reference: `libraries/AP_HAL_ChibiOS/hwdef/RangerH743/README.md`
- Sensor orientation: `ranger/docs/SENSOR_ORIENTATION.md`
- Open issues and limitations: `ranger/docs/OPEN_ISSUES.md`
- Hardware bring-up checklist: `ranger/docs/HARDWARE_BRINGUP.md`
- Hardware handoff snapshot: `ranger/hardware/handoff/`

## Workflow

- Work happens on `ranger/*` branches and reaches the default branch by
  pull request.
- To move to a newer ArduPilot release: `git fetch upstream tag <tag>`,
  then rebase or merge the Ranger branch onto it and re-run every tier.
- When the hardware team re-exports the handoff, replace
  `ranger/hardware/handoff/` and run the board tier. A failure there
  means the schematic and the firmware no longer agree.
- Upstream's own workflows also live in `.github/workflows/`. On a
  private fork they consume Actions minutes on every push; disable the
  ones you do not want with `gh workflow disable`.
