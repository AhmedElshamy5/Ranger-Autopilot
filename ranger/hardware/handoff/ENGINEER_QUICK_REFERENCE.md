# Ranger FC: Firmware Quick Reference (AS-DESIGNED, rev A0.1 placement)

**Not built, not routed, not tested.** Everything below is the intended electrical design, checked against the KiCad netlist (2026-11-11).

| # | Question | Answer |
|---|---|---|
| 1 | MCU | **STM32H743VIT6**, LQFP-100, 2 MB flash. HSE **8 MHz** crystal. No LSE crystal. Core supply: internal LDO |
| 2 | Primary IMU | **ICM-42688-P** (U5) on **SPI1**, CS **PA4**, INT1 **PC4**. Secondary: BMI088 (U6, optional fit) on SPI2 |
| 3 | Sensor buses | SPI1 = IMU1. SPI2 = BMI088 (CS accel **PD10**, gyro **PD11**; INT **PE10**, **PE12**). I2C2 (PB10/PB11) = **BMP390 @0x76**. I2C1 (PB8/PB9) = external, on the GPS connector. SPI4 = optical-flow connector (CS **PE4**, INT **PE3**) |
| 4 | UARTs | USART1 PB6/PB7 = **RC**. USART2 PD5/PD6 (+CTS PD3, RTS PD4) = **TELEM1**. USART3 PD8/PD9 = **Companion**. UART4 PA0/PA1 = **GPS**. USART6 PC6/PC7 = **LiDAR**. UART7 PE8/PE7 = spare test pads. UART8 RX PE0 = **ESC telemetry** (RX only) |
| 5 | ESC signals | **TIM1 CH1–CH4** = PE9, PE11, PE13, PE14 (AF1) → M1–M4. 100 k pull-downs. Motor-to-arm assignment is **not defined** |
| 6 | Servo signals | **TIM4 CH1–CH4** = PD12–PD15 (AF2) → S1–S4 through 100 Ω. Servo power is external |
| 7 | Battery sense | Voltage: **PC0 / ADC1_INP10**, V_bat = V_adc × 11. Current: **PC1 / ADC1_INP11** from the ESC's current output, **scale unknown**. 5 V rail: PC5 / ADC1_INP8, × 2 |
| 8 | CAN | **FDCAN1** PD0 (RX) / PD1 (TX), AF9 → SN65HVD230. **PC13** low = transceiver on. 120 Ω termination only if solder jumper JP1 is closed |
| 9 | Programming / debug | **SWD** 10-pin 1.27 mm (PA13, PA14, SWO PB3, NRST). **BOOT0 button** (SW1) + USB-C on PA11/PA12 for the ROM bootloader. VBUS sense on **PA9** (GPIO) |
| 10 | Still provisional | ESC connector pin order · servo connector type · motor numbering · IMU rotation relative to the airframe (board "forward" not fixed) · current-sense scale · board outline 46 mm · nothing is routed |

Other pins: LEDs **active low**: red PB2, green PD7, blue PE15. Buzzer **PA3** (TIM2_CH4, active high). Sensor-rail enable **PB12** (low = sensors off). microSD on **SDMMC1** (PC8–PC12, PD2), card detect PA10. IMU1 optional clock in from **PA8**.

IMU axes on the board (top side up): ICM-42688-P **+X → east, +Y → south, +Z → down**. BMI088 **+X → south, +Y → west, +Z → down**. See `SENSORS_AND_ORIENTATION.md` for the rotation per airframe orientation.

Full tables: `MCU_PINOUT.csv`, `UART_PORT_MAP.csv`, `CONNECTOR_PINOUTS.csv`, `MOTOR_SERVO_MAPPING.csv`, `PERIPHERAL_MAP.csv`.
