# RangerH743 hardware bring-up checklist

Nothing on this page has been done. No Ranger FC board exists yet. This
is the list of checks that software tests cannot replace, in the order
the hardware brief recommends. Record the result of each step here when
it is performed.

Rules for the whole session: props off, ESCs disconnected until step 10,
current-limited bench supply, 3.3 V serial adapters only.

| # | Check | How | Pass criterion | Result |
|---|---|---|---|---|
| 1 | Rails | Bench supply, no firmware | 5V_MAIN, VSYS, 3V3_MCU, 3V3_SENS in tolerance, no excess current | not done |
| 2 | SWD and bootloader | Flash `RangerH743_bl.bin` at 0x08000000 over J_SWD1 | Programmer connects, verify passes, bootloader LED blinks | not done |
| 3 | Clock | Bootloader enumerates on USB | USB works, so the 8 MHz HSE and PLL are right | not done |
| 4 | USB firmware load | Upload `arducopter.apj` through the ArduPilot bootloader | Upload completes, firmware boots | not done |
| 5 | ST ROM DFU | Hold BOOT0 (SW1), plug USB | Device appears as STM32 DFU. Until this passes, SWD is the only recovery path | not done |
| 6 | LEDs and buzzer | Boot | LEDs follow boot pattern (active low), buzzer plays the start tune. A constant tone or silence means the buzzer type differs from the PWM assumption | not done |
| 7 | ICM-42688-P | Boot messages, `INS_ACC_ID`, IMU data | Detected on SPI1, gyro and accel plausible, noise in datasheet range | not done |
| 8 | BMI088 (if fitted) | Same | Second IMU appears. Board also boots cleanly without it | not done |
| 9 | BMP390 | Baro data | Detected at 0x76 on I2C2, pressure matches local value, temperature plausible | not done |
| 10 | Sensor rail switch | Toggle PB12 | 3V3_SENS drops and recovers, sensors re-initialise | not done |
| 11 | microSD | Insert card, arm on the bench | Log file written and readable. Note card-detect level on PA10 with and without a card | not done |
| 12 | UARTs | Loopback or device on each connector | Data both ways on USART1/2/3/6, UART4, UART7; RX on UART8. CTS/RTS on TELEM1 | not done |
| 13 | CAN | DroneCAN node or analyser, JP1 as needed | Frames both ways at 1 Mbit/s; PC13 high puts the transceiver in standby | not done |
| 14 | Motor outputs | Scope on J_ESC1 pins 5-8, ESCs disconnected, motor test | Low during reset and boot; correct pulse on M1..M4 in order; 3.3 V level | not done |
| 15 | DShot | Scope or ESC with props off | Clean DShot frames at the chosen rate on all four outputs | not done |
| 16 | Servo outputs | Scope on J_S1..J_S4 | 50 Hz PWM on outputs 5-8 | not done |
| 17 | Battery voltage | Known supply voltage vs reported | Derive the real `BATT_VOLT_MULT`; replace the provisional 11.0 if needed | not done |
| 18 | 5 V rail reading | Multimeter vs reported board voltage | Within a few percent | not done |
| 19 | USB-only power | USB without battery | MCU, sensors and SD run; RC, GPS, telemetry, companion and LiDAR connectors unpowered, as designed | not done |
| 20 | Orientation | Tilt test in `SENSOR_ORIENTATION.md` | All four steps correct | not done |

Only after all of these pass, plus ESC, frame and failsafe configuration
for the real airframe, can a first tethered hover be considered.
