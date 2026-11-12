# Ranger FC: Firmware Brief (AS-DESIGNED, not built)

For the firmware engineer and their AI coding agent. Source of truth: the KiCad project in `KICAD/PROJECT/Ranger_FC.kicad_pro`. Pin data below was extracted from the exported netlist on 2026-11-11.

> **Status:** schematic complete (ERC 0 errors, 0 warnings). PCB placed and **partly routed (99 connections still open)**. **No board has been manufactured, powered or tested.** Everything here is intended design, not measured behaviour.

## 1. Board overview
| Item | Value |
|---|---|
| Board | Ranger FC, revision A0.1 |
| MCU | **STM32H743VIT6**, LQFP-100, 2 MB flash, 1 MB RAM |
| Clock | **8 MHz HSE crystal** on PH0/PH1. No 32.768 kHz crystal (use LSI) |
| Core supply | Internal LDO (VCAP pins 48, 73 with 2.2 µF). No SMPS on this package |
| Aircraft | Autonomous X-quad (MARVL indoor competition primary). ESCs and servo power are external |
| Rails | VBAT 2S–4S → **5V_MAIN** (LMR33630, 3 A) → **VSYS** (diode-OR with USB) → **3V3_MCU** (TLV62569, 2 A) and **3V3_SENS** (TPS7A2033 LDO, 300 mA, switchable) |

## 2. Hardware map
### Sensors
| Device | Ref | Bus | Pins | Notes |
|---|---|---|---|---|
| **ICM-42688-P** (primary IMU) | U5 | **SPI1** AF5 | SCK PA5, MISO PA6, MOSI PA7, **CS PA4**, **INT1 PC4** | ≤24 MHz. Pin 9 (INT2/FSYNC/CLKIN) ← **PA8** through 1 kΩ (optional external clock, leave Hi-Z if unused) |
| **BMI088** (secondary IMU, **optional fit**) | U6 | **SPI2** AF5 | SCK PB13, MISO PB14, MOSI PB15, **CS accel PD10**, **CS gyro PD11**, **INT accel PE10**, **INT gyro PE12** | ≤10 MHz. Accel needs one CS rising edge after power-up to enter SPI mode. Board must boot without it |
| **BMP390** baro | U7 | **I2C2** AF4 | SCL PB10, SDA PB11 | Address **0x76**. INT not connected. 2.2 kΩ pull-ups |

All three run on 3V3_SENS. **PB12 = sensor-rail enable** (100 k pull-up = on by default; drive low to power-cycle the sensors, after driving their bus pins low).

### Other buses
| Function | Peripheral | Pins | Notes |
|---|---|---|---|
| External I2C (GPS compass) | **I2C1** AF4 | SCL PB8, SDA PB9 | On the GPS connector, 2.2 kΩ pull-ups to 3.3 V |
| Optical flow (external SPI) | **SPI4** AF5 | SCK PE2, MISO PE5, MOSI PE6, CS PE4, INT PE3 | Off-board cable: keep ≤2 MHz |
| CAN | **FDCAN1** AF9 | RX PD0, TX PD1 | SN65HVD230 transceiver. **PC13 low = enabled** (high = standby). 120 Ω termination only if solder jumper JP1 is closed |
| USB | **OTG_FS** AF10 | DM PA11, DP PA12 | Device only. **VBUS sense on PA9 as plain GPIO** (10k/20k divider). USBLC6-2 ESD |
| microSD | **SDMMC1** AF12 | D0–D3 PC8–PC11, CK PC12, CMD PD2 | 4-bit, 3.3 V only, use internal pull-ups. **Card detect PA10** (switch to GND, polarity unconfirmed) |
| Debug | SWD | SWDIO PA13, SWCLK PA14, SWO PB3, NRST | 10-pin 1.27 mm Cortex header J_SWD1 |

### UARTs (all 3.3 V, direct to the MCU, no inverters)
| UART | TX | RX | Connector (pins: 1 = 5 V, last = GND) | Purpose |
|---|---|---|---|---|
| **USART1** AF7 | PB6 | PB7 | J_RC1: 2 = RC_RX (FC in), 3 = RC_TX | RC receiver (CRSF/ELRS; SBUS needs USART RX inversion) |
| **USART2** AF7 | PD5 | PD6 | J_TELEM1: 2 TX, 3 RX, 4 CTS (PD3), 5 RTS (PD4) | Telemetry radio / Wi-Fi bridge |
| **USART3** AF7 | PD8 | PD9 | J_COMP1: 2 TX, 3 RX, 4 spare GPIO PB5 | Companion computer (OpenMV N6) |
| **UART4** AF8 | PA0 | PA1 | J_GPS1: 2 TX, 3 RX, 4 SCL, 5 SDA | GPS (+ compass on I2C1) |
| **USART6** AF7 | PC6 | PC7 | J_LIDAR1: 2 TX, 3 RX | Rangefinder (TFmini-S) |
| **UART7** AF7 | PE8 | PE7 | Test pads TP1/TP2 only | Spare / debug console |
| **UART8** AF8 | (PE1 not connected) | PE0 | J_ESC1 pin 4 | ESC telemetry, **RX only** |

Enable internal pull-ups on all RX pins. 5 V-tolerant RX pins (DS12110 FT type): PB7, PD6, PD9, PC7, PE0. **PE7 is not 5 V tolerant; PA1 is unconfirmed.**

### Outputs and GPIO
| Function | Pins | Notes |
|---|---|---|
| Motors M1–M4 | see §4 | TIM1 |
| Servos S1–S4 | **PD12, PD13, PD14, PD15** = **TIM4 CH1–CH4** (AF2) | 100 Ω series. Headers J_S1–J_S4: pin 1 GND, 2 SERVO_5V (external BEC, not from the FC), 3 signal |
| Buzzer | **PA3** = TIM2_CH4 (AF1) | Active high, drives a 2N7002 low-side switch |
| LEDs | red **PB2**, green **PD7**, blue **PE15** | **Active low** |
| BOOT0 | pin 94 | 10 k pull-down, button SW1 to 3.3 V. **No reset button** |
| Unused | PA2, PA15, PB0, PB1, PB4, PC2_C, PC3_C, PC14, PC15, PE1 | Not connected |

## 3. Sensor orientation
Board frame (top view, MCU side up): **north** edge = CAN + USB-C, **south** = ESC + LiDAR, **west** = TELEM1 + RC, **east** = companion + servos. Both IMUs and the baro are on the **bottom** side.

| Sensor | +X | +Y | +Z |
|---|---|---|---|
| ICM-42688-P | east | south | down |
| BMI088 | south | west | down |

Derived from the PCB pad coordinates and the datasheet axis figures (DS-000347 Fig. 16; Bosch DS000-19 Fig. 12). **Which board edge faces the aircraft's nose is not defined yet**, so the final rotation setting is open. Confirm with a physical tilt test before flight. `SENSORS_AND_ORIENTATION.md` lists the rotation for each possible forward edge.

## 4. Motor and timer mapping
| Output | MCU pin | Timer / channel | AF | ESC connector J_ESC1 pin |
|---|---|---|---|---|
| M1 | PE9 | TIM1_CH1 | 1 | 5 |
| M2 | PE11 | TIM1_CH2 | 1 | 6 |
| M3 | PE13 | TIM1_CH3 | 1 | 7 |
| M4 | PE14 | TIM1_CH4 | 1 | 8 |

J_ESC1 (JST-SH 8-pin): 1 VBAT, 2 GND, 3 current sense, 4 ESC telemetry, 5–8 M1–M4. **This pin order is provisional** (ESC not selected), and **M1–M4 are not assigned to aircraft arms.** All four share TIM1, so one protocol and rate (DShot/PWM) for all. 100 kΩ pull-downs hold them low during reset. DMA: the H7 DMAMUX can route TIM1_UP / TIM1_CHx to any free DMA1/2 stream; nothing in the hardware reserves a stream.

## 5. Power and ADC
| Signal | Pin | ADC channel | Scaling |
|---|---|---|---|
| Battery voltage | **PC0** | ADC1_INP10 | **V_bat = V_adc × 11.0** (100 kΩ / 10 kΩ, 1 %). Calibrate per board |
| Battery current | **PC1** | ADC1_INP11 | From the ESC's current output via 1 kΩ + 100 nF. **No current sensor on the FC; scale unknown until the ESC is chosen** |
| 5 V rail | **PC5** | ADC1_INP8 | V_5V = V_adc × 2.0 |

ADC reference VREF+ = VDDA = 3.3 V rail through a ferrite bead (not a precision reference). Battery range 2S–4S as designed; the 5 V buck enables above about 5.8 V and stops below about 5.3 V. **On USB power alone only the MCU, sensors and microSD run; the RC receiver, GPS, telemetry, companion and LiDAR connectors have no 5 V.** MCU VBAT is tied to 3.3 V: no RTC backup.

## 6. Firmware development recommendations (suggestions, not hardware facts)
- Target: STM32H743xx, 8 MHz HSE, internal-LDO supply configuration.
- ArduPilot is the team's working proposal (decision ED-14, not confirmed). Investigate a ChibiOS `hwdef.dat` board port, starting from an existing H743 board with an 8 MHz crystal, and replace every pin with the tables above. Treat ArduPilot's acceptance under the ICMTC "designed from scratch" rule as an open question for the team.
- Bring-up order: clocks and LEDs → SWD logging → USB CDC → SPI1 ICM-42688-P WHO_AM_I → I2C2 BMP390 → SDMMC1 → UARTs → FDCAN1 → TIM1 outputs (scope, motors disconnected) → ADC.
- IMU instance order: ICM-42688-P first, BMI088 second; probing a missing BMI088 must not block boot.
- Use SITL for flight logic; hardware-specific code (pins, DMA, drivers) needs the physical board.

## 7. Known limitations and open decisions
- Motor numbering and ESC connector pin order are not final.
- IMU-to-airframe rotation needs the mechanical forward direction and a tilt test.
- No current sensor on the board; current scale depends on the ESC.
- USB DFU via the ST ROM bootloader (BOOT0 + USB) is expected but unconfirmed; SWD is the guaranteed programming path.
- PA1 (GPS RX) 5 V tolerance unconfirmed; use 3.3 V GPS modules.
- microSD card-detect polarity unconfirmed.
- Flow-sensor connector pin order unverified; servo connector type provisional.
- Crystal part not yet selected (8 MHz, CL 10 pF intended).
- PCB not fully routed; board outline 46 × 46 mm is provisional. Not manufactured, not tested.

## 8. Instructions to the firmware AI agent
1. Read this brief completely before writing code.
2. Verify any mapping you rely on against `FIRMWARE_HANDOFF/MCU_PINOUT.csv`, `CONNECTOR_PINOUTS.csv`, `ENGINEERING/PIN_ALLOCATION_ACTUAL.csv` and the datasheets in `ENGINEERING/DATASHEETS/`. If they disagree, stop and report.
3. Set up a reproducible build environment (pinned toolchain and dependency versions, one-command build).
4. Create the Ranger STM32H743 board configuration from the pins above only. Do not copy pins from another board.
5. Implement and unit-test drivers for verified peripherals first.
6. Add SITL and automated tests wherever hardware is not required.
7. Keep a list of unresolved hardware dependencies (everything in §7) and update it as decisions are made.
8. Never treat a provisional assignment as final.
9. Never claim hardware testing or flight readiness without a real board.
