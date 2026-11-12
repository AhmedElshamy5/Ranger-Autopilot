# Firmware Integration Guide (hardware inputs and recommendations)

These are hardware facts plus recommendations. No board definition has been built or compiled for this board, and no firmware platform has been chosen by the team (ArduPilot is the working proposal, ED-14).

## Board definition inputs
| Item | Value |
|---|---|
| MCU | STM32H743VIT6 (STM32H7xx / STM32H743xx), LQFP-100 |
| Flash | 2048 kB |
| Oscillator | HSE crystal, 8 000 000 Hz |
| Core supply | Internal LDO (no SMPS on this package) |
| USB | OTG_FS on PA11/PA12, device. VBUS detect on PA9 as GPIO |
| microSD | SDMMC1, 4-bit, internal pull-ups on CMD/D0–D3 |
| Debug | SWD on PA13/PA14. Keep them reserved |
| Board ID | **Not allocated.** A custom ID is needed for an ArduPilot bootloader |

## Bus initialisation
- **SPI1** (PA5/PA6/PA7 AF5): ICM-42688-P only. CS PA4, idle high (10 k pull-up to the sensor rail). Data-ready on PC4.
- **SPI2** (PB13/PB14/PB15 AF5): BMI088. Two chip selects, PD10 (accel) and PD11 (gyro). The accelerometer needs a rising edge on its CS after power-up before it answers on SPI; do a dummy read.
- **I2C2** (PB10/PB11 AF4): BMP390 at 0x76, 400 kHz, pull-ups fitted.
- **I2C1** (PB8/PB9 AF4): external compass on the GPS connector, pull-ups fitted.
- **SPI4** (PE2/PE5/PE6 AF5): external flow module, CS PE4. Slow clock because of the cable.
- **FDCAN1** (PD0/PD1 AF9): drive PC13 low to enable the transceiver. PC13 is a low-drive pin, so set it once and leave it.
- **Sensor rail**: PB12 high (or input/Hi-Z) = on. Configure it early; the rail is on by default through the pull-up.

## UART mapping
See `UART_PORT_MAP.csv`. All ports are 3.3 V, direct to the MCU, no inverters. Enable the internal pull-up on every RX pin. SBUS on the RC port needs the USART's RX inversion.

Suggested ArduPilot order (recommendation, to be approved by the firmware engineer): SERIAL0 = USB, SERIAL1 = USART2 (TELEM1), SERIAL2 = USART3 (Companion), SERIAL3 = UART4 (GPS), SERIAL4 = USART6 (LiDAR), SERIAL5 = USART1 (RC), SERIAL6 = UART7 (test pads), SERIAL7 = UART8 (ESC telemetry, RX only).

## IMU and baro
- IMU order: ICM-42688-P first, BMI088 second (and absent on boards where it is not fitted: probing must not block boot).
- Rotation: see `SENSORS_AND_ORIENTATION.md`. It depends on which board edge faces forward, which is not fixed yet.
- ICM-42688-P pin 9 is wired to PA8 through 1 kΩ. Leave PA8 as an input unless the sensor's CLKIN feature is used.
- Baro: BMP390, I2C address 0x76.

## Motors
- TIM1 CH1–CH4 on PE9, PE11, PE13, PE14 (AF1), all on one timer, so one output protocol and rate for the four motors.
- DMA: on the H7 any DMA1/DMA2 stream can serve any request through DMAMUX1. For DShot the firmware needs TIM1_UP (or the four TIM1_CHx requests for bidirectional DShot). Nothing in the hardware reserves or blocks a stream.
- 100 kΩ pull-downs hold the ESC inputs low while the MCU is in reset.
- **Motor numbering vs. arms is not defined by the hardware.** M1–M4 are simply ESC connector pins 5–8, and that pin order is provisional until the ESC is chosen. Map motors in firmware once the ESC and its orientation are known.

## Servos
TIM4 CH1–CH4 on PD12–PD15 (AF2), 3.3 V, 100 Ω series. Standard positive pulses. Servo power is external; the FC cannot switch or measure it.

## Battery monitor
Voltage on ADC1 channel 10 (PC0), multiplier 11.0. Current on ADC1 channel 11 (PC1), scale unknown. Details and caveats in `POWER_AND_ADC.md`.

## Other GPIO
| Function | Pin | Polarity |
|---|---|---|
| LED red / green / blue | PB2 / PD7 / PE15 | Active low |
| Buzzer | PA3 (TIM2_CH4, AF1) | Active high |
| microSD detect | PA10 | Switch to GND; confirm level on hardware |
| Companion spare GPIO | PB5 | — |
| CAN standby | PC13 | High = standby |
| Sensor rail enable | PB12 | Low = off |

## Unused MCU pins
PA2, PA15, PB0, PB1, PB4, PC2_C, PC3_C, PC14, PC15, PE1 are not connected. Configure them as analog or pulled inputs.

## Constraints to respect
- PE7 (UART7 RX test pad) is not 5 V tolerant.
- No external 5 V logic should reach PA1 (GPS RX) until its tolerance is confirmed.
- 5 V peripherals are unpowered on USB alone; do not drive their signal pins high for long in that state.
- There is no hardware watchdog or reset supervisor beyond the MCU's own.
