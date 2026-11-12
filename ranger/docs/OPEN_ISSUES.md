# RangerH743 open issues and limitations

The Ranger FC A0.1 is an unmanufactured prototype. The firmware in this
repository has been compiled and its flight logic exercised in
simulation. It has never run on a Ranger board.

## Source-document gaps

| # | Issue | Effect on firmware |
|---|---|---|
| D1 | The handoff folder (snapshot in `ranger/hardware/handoff/`) was used and its CSVs agree with the firmware pin map. Not available: `ENGINEERING/PIN_ALLOCATION_ACTUAL.csv`, the datasheet folder and the KiCad project itself | The firmware relies on the netlist-generated CSVs, not on a direct reading of the schematic. Datasheet limits (SPI clocks, addresses) are taken from the handoff text |
| D2 | The handoff documents disagree on routing progress: the brief says "partly routed (99 connections still open)", `HARDWARE_STATUS.md` says "371 connections unrouted" and the README says "not routed" | No effect on pins, which come from the schematic netlist. It does mean pins can still move: re-export the CSVs into `ranger/hardware/handoff/` and re-run `ranger/tests/board` after any schematic change |

## Open hardware decisions (firmware left provisional)

| # | Decision | Current firmware behaviour | To close |
|---|---|---|---|
| H1 | Motor numbering and J_ESC1 pin order | Outputs 1-4 = TIM1 CH1-4 = M1-M4. No frame class, no motor order. Vehicle will not arm until `FRAME_CLASS` is set | Select ESC, fix arm assignment, then set frame parameters or remap outputs |
| H2 | Which board edge faces the nose | Sensors rotated into a board frame only. `AHRS_ORIENTATION` not set | Mechanical decision, then tilt test (`SENSOR_ORIENTATION.md`) |
| H3 | Battery voltage scale | `BATT_VOLT_MULT` default 11.0, which is the schematic divider (100k top / 10k bottom, 1 %). Expect about +/-2 % plus VDDA tolerance, since VREF+ is the 3.3 V supply | Calibrate against a multimeter on each board |
| H4 | Battery current | No sensor on the FC. PC1 is mapped as an ADC input (channel 11) but no default current pin or scale is defined, so current sensing is off | Choose ESC; use its analog scale or its telemetry |
| H5 | ESC protocol | Default PWM type untouched. DShot is compiled in and TIM1 has a DMA channel allocated, but no DShot frame has been observed | ESC selection, then scope check |
| H6 | ESC telemetry | UART8 RX mapped as SERIAL6 with protocol None | ESC selection |
| H7 | BMI088 fit | Probed as second IMU; absent part is skipped | Population decision |
| H8 | Buzzer type | Driven as a PWM tone on TIM2_CH4 | Confirm passive buzzer; switch to GPIO if active |
| H9 | microSD card-detect polarity | PA10 pulled up, unused | Measure on a board |
| H10 | Optical-flow module (PMW3901 intended) and J_FLOW1 pin order | SPI4 mapped and a Pixart flow device declared at 2 MHz. It is only probed if `FLOW_TYPE` is set; no default sets it | Confirm module and pin order, then enable `FLOW_TYPE` |
| H11 | Crystal part | 8 MHz HSE assumed | Part selection; check start-up on a board |
| H12 | PA1 (GPS RX) 5 V tolerance | Not a firmware matter | Use 3.3 V GPS modules |
| H13 | USB DFU through the ST ROM | Not relied on. SWD is the programming and recovery path | Test on a board |

## Firmware limitations

| # | Limitation |
|---|---|
| F1 | Board ID 20743 (`AP_HW_RANGERH743`) is local to this fork and not allocated by ArduPilot. Ground stations will not recognise the board by name. Request an ID upstream before distributing firmware |
| F2 | The IMU interrupt lines (PC4, PE10, PE12) and the ICM-42688-P CLKIN line (PA8) are mapped as inputs but unused: the upstream drivers poll the sensor FIFOs |
| F3 | RC input is serial only (USART1). There is no timer-capture RC pin, so PPM is not supported. SBUS needs the UART RX inversion option |
| F4 | No RTC backup (MCU VBAT tied to 3.3 V, no LSE). Time comes from GPS or the ground station |
| F5 | No compass on the board. Arming without a compass is allowed by the board definition; an external compass on the GPS connector is probed automatically |
| F6 | Low-rate ports (USART6, UART7, UART8) run without DMA to leave DMA channels for the IMUs, DShot and the high-rate links |
| F7 | The SITL vehicle is a generic simulated quad, not a model of the Ranger airframe |
| F8 | Whether ArduPilot is acceptable under the ICMTC "designed from scratch" rule is an open team question (hardware brief, decision ED-14) |
| F9 | The repository was created as a shallow clone of the `Copter-4.7.2` tag because of a poor connection. Run `git fetch --unshallow upstream` to pull full upstream history |

## What has and has not been verified

| Claim | Verified? | How |
|---|---|---|
| hwdef matches the handoff's netlist-generated `MCU_PINOUT.csv` and `UART_PORT_MAP.csv` | Yes | `ranger/tests/board` |
| Alternate functions exist on the STM32H743 | Yes | Same tests, against upstream's H743 AF table |
| Firmware and bootloader compile and link for RangerH743 | Yes (2026-11-12, gcc-arm-none-eabi 10-2020-q4, about 1.51 MB of flash used) | `ranger/scripts/build_fw.sh`, `ranger/tests/outputs` |
| DShot, sensor, CAN and SD drivers are linked into the image | Yes | symbol check on the ELF |
| Flight logic, failsafe and logging defaults | In simulation only | `ranger/tests/sitl` |
| Any sensor, bus, output, USB or power behaviour on the PCB | **No** | Needs a board: `HARDWARE_BRINGUP.md` |
| Flight readiness | **No** | |
