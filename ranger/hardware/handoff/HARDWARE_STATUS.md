# Hardware Status (2026-11-11)

"The Ranger Flight Controller is currently an unmanufactured, unrouted or partially routed engineering prototype. This document describes the intended electrical design and is not evidence of physical hardware operation."

Statuses describe **logical connectivity in the design files**. Nothing has been manufactured or powered.

| Feature | Status | Note |
|---|---|---|
| MCU STM32H743VIT6, power pins, VCAP, decoupling | CONFIRMED_IN_SCHEMATIC | Checked against DS12110 Rev 11 |
| 8 MHz HSE | CONFIRMED_IN_SCHEMATIC | Crystal part number not selected |
| Reset, BOOT0 button | CONFIRMED_IN_SCHEMATIC | No reset button |
| SWD header | CONFIRMED_IN_PCB_PLACEMENT | Bottom side |
| USB-C device, ESD, VBUS sense | CONFIRMED_IN_PCB_PLACEMENT | ROM DFU not verified |
| ICM-42688-P on SPI1 | CONFIRMED_IN_PCB_PLACEMENT | Pinout checked against DS-000347 v1.9 |
| IMU axis mapping to the board | CONFIRMED_IN_PCB_PLACEMENT | Rotation to the airframe is PROVISIONAL |
| BMI088 on SPI2 | OPTIONAL | Stock risk |
| BMP390 on I2C2 | CONFIRMED_IN_PCB_PLACEMENT | |
| Magnetometer | NOT_IMPLEMENTED | External only |
| microSD (SDMMC1) | CONFIRMED_IN_PCB_PLACEMENT | Card-detect polarity UNVERIFIED |
| USART1 RC, USART2 TELEM1, USART3 Companion, UART4 GPS, USART6 LiDAR | CONFIRMED_IN_SCHEMATIC | Connector pin order follows the common Pixhawk layout; standard not re-read |
| UART7 test pads | CONFIRMED_IN_SCHEMATIC | |
| UART8 ESC telemetry RX | PROVISIONAL | ESC connector order |
| FDCAN1 + SN65HVD230 + JP1 termination | CONFIRMED_IN_SCHEMATIC | |
| SPI4 flow connector | PROVISIONAL | Module pin order not verified |
| Motor outputs TIM1 CH1–4 | CONFIRMED_IN_SCHEMATIC | Connector order and motor numbering PROVISIONAL |
| DShot / bidirectional DShot | UNVERIFIED | Pins are timer-capable; never tested |
| Servo outputs TIM4 CH1–4 | CONFIRMED_IN_SCHEMATIC | Connector type and position PROVISIONAL |
| Battery voltage sense | CONFIRMED_IN_SCHEMATIC | Needs calibration |
| Battery current sense | UNVERIFIED | Depends on the ESC; no scale |
| 5 V rail sense | CONFIRMED_IN_SCHEMATIC | |
| 5 V / 3.3 V / sensor rails | CONFIRMED_IN_SCHEMATIC | Several power parts still without a selected MPN |
| Sensor-rail switch (PB12) | CONFIRMED_IN_SCHEMATIC | |
| Buzzer driver, LEDs | CONFIRMED_IN_SCHEMATIC | |
| LED strip output | NOT_IMPLEMENTED | Removed (ED-17) |
| Board outline 46 × 46 mm, hole pattern | PROVISIONAL | Not approved by mechanical |
| PCB routing, planes | NOT_IMPLEMENTED | 371 connections unrouted |
| Layer stackup, USB impedance | PROVISIONAL | No fab stackup |
| Physical operation of anything | UNVERIFIED | No hardware exists |
