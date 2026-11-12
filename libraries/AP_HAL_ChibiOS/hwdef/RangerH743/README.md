# RangerH743 (Ranger FC A0.1)

Custom flight controller by Ranger UAV. This directory is Ranger-developed;
the drivers and everything else it uses are unmodified upstream ArduPilot.

> **Status: as-designed.** No Ranger FC board has been manufactured,
> powered or tested. This port compiles and its pin map is checked
> against the hardware handoff, but it has never run on hardware. Open
> points are listed in [`ranger/docs/OPEN_ISSUES.md`](../../../../ranger/docs/OPEN_ISSUES.md).

## Hardware summary

| Item | Value |
|---|---|
| MCU | STM32H743VIT6, LQFP-100, 2 MB flash, 8 MHz HSE, no LSE |
| IMU 1 | ICM-42688-P on SPI1 |
| IMU 2 | BMI088 on SPI2, optional fit |
| Barometer | BMP390 on I2C2, address 0x76 |
| Compass | none on board; external on the GPS connector (I2C1) |
| Storage | microSD on SDMMC1 (4 bit); parameters in internal flash |
| Outputs | 4 motor (TIM1), 4 servo (TIM4), buzzer, RGB LED |
| Interfaces | USB-C (FS device), 7 UARTs, FDCAN1, external I2C, external SPI |
| Power | 2S-4S battery. USB powers the MCU, sensors and microSD only |

## Serial port mapping

| Firmware port | MCU UART | Pins (TX/RX) | Connector | Default protocol | DMA |
|---|---|---|---|---|---|
| SERIAL0 | USB OTG_FS | PA12/PA11 | J_USB1 | MAVLink2 | - |
| SERIAL1 | USART2 | PD5/PD6, CTS PD3, RTS PD4 | J_TELEM1 | MAVLink2 | yes |
| SERIAL2 | USART3 | PD8/PD9 | J_COMP1 | MAVLink2, 921600 | yes |
| SERIAL3 | UART4 | PA0/PA1 | J_GPS1 | GPS | yes |
| SERIAL4 | USART6 | PC6/PC7 | J_LIDAR1 | Rangefinder | no |
| SERIAL5 | USART1 | PB6/PB7 | J_RC1 | RC input | yes |
| SERIAL6 | UART7 | PE8/PE7 | TP1/TP2 | None | no |
| SERIAL7 | UART8 | -/PE0 (RX only) | J_ESC1 pin 4 | None | no |

This is the numbering suggested in the hardware handoff
(`UART_PORT_MAP.csv`). All ports are 3.3 V with no inverters. The
generator enables the internal pull-up on every RX pin. PE7 is not 5 V
tolerant and PA1's tolerance is unconfirmed.

SERIAL4 defaults to the rangefinder protocol because J_LIDAR1 is a
dedicated connector, but `RNGFND1_TYPE` is left at 0, so no rangefinder
is active until one is configured. SERIAL7 stays at None until an ESC
is selected.

RC input is serial only (CRSF/ELRS and similar). There is no PPM
capture pin. SBUS needs RX inversion through `SERIAL5_OPTIONS`.

## PWM outputs

| Output | Pin | Timer | Connector | Notes |
|---|---|---|---|---|
| 1 | PE9 | TIM1_CH1 | J_ESC1 pin 5 (M1) | |
| 2 | PE11 | TIM1_CH2 | J_ESC1 pin 6 (M2) | |
| 3 | PE13 | TIM1_CH3 | J_ESC1 pin 7 (M3) | |
| 4 | PE14 | TIM1_CH4 | J_ESC1 pin 8 (M4) | |
| 5 | PD12 | TIM4_CH1 | J_S1 | servo signal only |
| 6 | PD13 | TIM4_CH2 | J_S2 | servo signal only |
| 7 | PD14 | TIM4_CH3 | J_S3 | servo signal only |
| 8 | PD15 | TIM4_CH4 | J_S4 | servo signal only |

Outputs 1-4 share TIM1 and outputs 5-8 share TIM4, so each group runs
one protocol and one rate.

**Motor order is provisional.** M1-M4 are ESC connector pins, not
airframe arms, and the connector pin order is not final. The board
defaults set no frame class and no output functions.

**DShot:** TIM1_UP has its own DMA stream (see below), which is what
ArduPilot's DShot output needs, and the firmware is built with DShot
support. No DShot signal from this board has ever been observed, so
treat it as untested. Bidirectional DShot is not configured.

**Servos:** the FC provides the 3.3 V signal only. Servo power comes
from an external BEC on the SERVO_5V pins and is not connected to the
FC's 5 V rail.

## DMA allocation

Produced by ArduPilot's resolver for this hwdef (the H7 DMAMUX lets any
request use any stream; the limit is 16 streams in total).

| Stream | Request |
|---|---|
| DMA1 S0 | TIM1_UP (motor outputs, not shared) |
| DMA1 S1 | SPI1_RX (ICM-42688-P, not shared) |
| DMA1 S2 | SPI1_TX (ICM-42688-P, not shared) |
| DMA1 S3 | ADC1 |
| DMA1 S4 | USART2_RX |
| DMA1 S5 | USART3_RX |
| DMA1 S6 | UART4_RX |
| DMA1 S7 | USART1_RX |
| DMA2 S0 | SPI4_TX |
| DMA2 S1 | USART2_TX |
| DMA2 S2 | USART1_TX |
| DMA2 S3 | SPI2_TX |
| DMA2 S4 | UART4_TX |
| DMA2 S5 | SPI4_RX, shared with TIM4_UP |
| DMA2 S6 | USART3_TX |
| DMA2 S7 | SPI2_RX |

All 16 streams are in use. The only shared stream is between the
external flow SPI and the servo timer. USART6, UART7 and UART8 are
declared `NODMA` to make this fit; they are low-rate ports. I2C runs
without DMA on the H7. The SD card uses the SDMMC internal DMA.

## Analog inputs

| Pin | ADC channel | Signal | Scale |
|---|---|---|---|
| PC0 | 10 | Battery voltage | x11.0 (100k/10k), `BATT_VOLT_MULT` default |
| PC1 | 11 | ESC current output | none: no current sensor on the FC |
| PC5 | 8 | 5 V rail | x2.0 (10k/10k) |

The battery monitor defaults to voltage only (`BATT_MONITOR` = 3). The
ADC reference is the 3.3 V supply, not a precision reference, so
calibrate `BATT_VOLT_MULT` per board. To use the ESC's analog current
output later, set `BATT_MONITOR` = 4, `BATT_CURR_PIN` = 11 and
`BATT_AMP_PERVLT` from the ESC's datasheet.

## Sensor orientation

`hwdef.dat` rotates both IMUs into a board frame whose X axis is the
USB-C/CAN edge. The edge that faces the aircraft's nose is not decided,
so `AHRS_ORIENTATION` is not set. See
[`ranger/docs/SENSOR_ORIENTATION.md`](../../../../ranger/docs/SENSOR_ORIENTATION.md).

## Other pins

| Function | Pin | Notes |
|---|---|---|
| Sensor rail enable | PB12 | high = on (board default) |
| CAN transceiver RS | PC13 | low = active, high = standby |
| USB VBUS sense | PA9 | GPIO through 10k/20k divider |
| LED red / green / blue | PB2 / PD7 / PE15 | active low |
| Buzzer | PA3 (TIM2_CH4) | PWM tone, active high |
| microSD card detect | PA10 | pulled up, not used (polarity unconfirmed) |
| ICM-42688-P CLKIN | PA8 | input, high impedance, not used |
| IMU interrupts | PC4, PE10, PE12 | inputs, not used (drivers poll) |
| Companion spare GPIO | PB5 | input, GPIO 81 |
| Flow interrupt | PE3 | input, not used |
| Unconnected pins | PA2, PA15, PB0, PB1, PB4, PC2, PC3, PC14, PC15, PE1 | inputs with pull-down |

## Building

```
ranger/scripts/build_fw.sh
```

or by hand:

```
./waf configure --board RangerH743
./waf copter
```

The bootloader binary is committed in `Tools/bootloaders/`. Rebuild it
after changing `hwdef-bl.dat` with
`ranger/scripts/build_fw.sh --rebuild-bootloader` and commit the result.

Outputs are in `build/RangerH743/bin/`. `arducopter_with_bl.hex`
contains bootloader and firmware in one image.

## Programming

**SWD is the only programming path this port relies on.** Connector
J_SWD1 (ARM 10-pin, 1.27 mm).

- Blank board: flash `arducopter_with_bl.hex` over SWD, or flash
  `Tools/bootloaders/RangerH743_bl.bin` at `0x08000000`.
- Once the ArduPilot bootloader is running, firmware updates can go
  over USB with any ground station by loading `arducopter.apj`. This
  has not been tried on a Ranger board.
- ST ROM DFU (hold SW1/BOOT0 while plugging in USB; there is no reset
  button) is expected to work on the H743 but is unconfirmed here. Do
  not depend on it for recovery until it has been tested.

The board ID (`AP_HW_RANGERH743`, 20743) is local to this fork and not
registered with ArduPilot.
