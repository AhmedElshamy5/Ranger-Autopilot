# Sensors and Orientation (AS-DESIGNED, A0.1 placement)

Source: pad coordinates read from `Ranger_FC.kicad_pcb` on 2026-11-11, and the axis figures in the datasheets (DS-000347 Fig. 5 and Fig. 16; BST-BMI088-DS000-19 Fig. 11, Fig. 12, Table 15). Positions will move slightly during routing; **re-check this file if a sensor footprint is rotated or flipped.**

## Board frame used here
Looking at the **top side** (MCU side), with the board edges named as on the PCB drawing:
- **North** = edge with CAN + USB-C. **South** = ESC + LiDAR. **West** = TELEM1 + RC. **East** = Companion + servo headers.
- "Down" = out of the bottom side (the side with the IMUs and microSD).

The airframe's forward direction relative to these edges is **not defined in the mechanical CAD**, so the rotation is given for all four cases.

## Sensors
| | IMU1 | IMU2 | Baro |
|---|---|---|---|
| Part | ICM-42688-P (U5) | BMI088 (U6), **optional fit** | BMP390 (U7) |
| Bus | SPI1, mode 0/3, ≤24 MHz | SPI2, ≤10 MHz | I2C2, address **0x76** (SDO = GND) |
| CS | PA4 | accel PD10 (CSB1), gyro PD11 (CSB2) | CSB tied high (I2C) |
| Interrupts | INT1 → PC4. Pin 9 (INT2/FSYNC/CLKIN) ← PA8 through 1 kΩ | accel INT1 → PE10, gyro INT3 → PE12. INT2, INT4 unconnected | INT not connected |
| Supply | 3V3_SENS (VDD and VDDIO) | 3V3_SENS | 3V3_SENS |
| Decoupling | 100 nF + 2.2 µF, 100 nF | 100 nF × 2 | 100 nF × 2 |
| PCB side | **Bottom** | **Bottom** | **Bottom** |
| Position from board centre | 0, 0 (centroid) | 4.2 mm south | 5.4 mm east, 0.8 mm north |
| Footprint rotation | 0° (flipped) | 0° (flipped) | 0° (flipped) |

All three share the 3V3_SENS rail, which the MCU can switch with **PB12** (low = off). Drive the sensor bus pins low before switching it off.

## Sensor axes on the board (top side up)
| Sensor | +X points | +Y points | +Z points |
|---|---|---|---|
| ICM-42688-P | **east** | **south** | **down** |
| BMI088 (accel and gyro) | **south** | **west** | **down** |

How this was derived:
- ICM-42688-P: in the datasheet top view, pin 1 is top-left, +X runs toward pins 8–11 and +Y toward pins 12–14. On the PCB, pins 1→4 run north and pins 8–11 are on the east side.
- BMI088: in Fig. 11, +X runs toward pins 1–7 and +Y toward pin 16. On the PCB, pins 1–7 are on the south side and pin 16 on the west.
- Both are on the bottom, so the package top (+Z) faces down. Both results are right-handed.

## Rotation to a body frame (X forward, Y right, Z down), board top side up
| Airframe forward = | ICM-42688-P | BMI088 |
|---|---|---|
| North edge (CAN/USB) | YAW_90 | YAW_180 |
| East edge | NONE | YAW_90 |
| South edge (ESC) | YAW_270 | NONE |
| West edge | YAW_180 | YAW_270 |

Names follow ArduPilot's `ROTATION_*` convention applied to the datasheet axes. **Firmware drivers may apply their own internal axis conversion**, so confirm with a tilt test on the first board (pitch nose-down, roll right, check signs) before any flight.

## Barometer
- The BMP390 vent is on the package lid, which faces **down** from the bottom side.
- It is light- and airflow-sensitive in general practice: plan an open-cell foam cover. The datasheet's own mounting guidance was not re-read for this.
- It sits about 13 mm from the 5 V inductor and under the MCU, so expect self-heating offsets; calibrate after warm-up.

## Not on the board
- No magnetometer. Use the external compass on the GPS connector (I2C1).
- Optical flow and LiDAR are external modules (SPI4 and USART6).
