# Power and ADC (AS-DESIGNED)

## Rails
| Rail | Source | Nominal | Capacity | Feeds | Notes |
|---|---|---|---|---|---|
| VBAT (+BATT) | J_ESC1 pin 1 or J1 pads | 6.0–16.8 V (2S–4S) | — | 5 V buck, VBAT divider | P-FET reverse protection, SMBJ20A TVS. Buck enables above 5.79 V, drops out below 5.32 V |
| 5V_MAIN (+5V) | LMR33630B buck, 1.4 MHz | 5.02 V | 3 A | 5 V pins of RC, TELEM1, Companion, GPS, LiDAR, CAN; buzzer | **Only present on battery.** Not powered from USB |
| VSYS | 5V_MAIN or USB VBUS through Schottky diodes | ≈4.5–4.7 V | — | 3V3 buck, sensor LDO | Lets the MCU and sensors run from USB alone |
| 3V3_MCU (+3V3) | TLV62569 buck | 3.318 V | 2 A | MCU, microSD, CAN transceiver, LEDs, flow connector pin 1, SWD VTref | |
| 3V3_SENS | TPS7A2033 LDO | 3.3 V | 300 mA | ICM-42688-P, BMI088, BMP390, I2C2 pull-ups | Enable = **PB12** (100 k pull-up: on by default) |
| 3.3VA | 3V3_MCU through a ferrite bead | 3.318 V | — | VDDA, **VREF+** | ADC reference is the supply, not a precision reference |
| SERVO_5V | External BEC on any servo header | external | external | Servo header pin 2 only | **Not connected to 5V_MAIN** |

USB-only operation: MCU, sensors and microSD work. RC receiver, GPS, companion, LiDAR and telemetry radios are **unpowered** until a battery is connected.

## ADC channels (ADC1, 16-bit capable, VREF+ = VDDA ≈ 3.32 V)
| Signal | Pin | Channel | Circuit | Equation | Range |
|---|---|---|---|---|---|
| Battery voltage | PC0 | ADC1_INP10 | 100 kΩ (top) / 10 kΩ (bottom), 100 nF | **V_bat = V_adc × 11.0** | 16.8 V → 1.527 V. Full scale ≈ 36 V |
| Battery current | PC1 | ADC1_INP11 | 1 kΩ series + 100 nF from J_ESC1 pin 3 | **I = V_adc × K**, K set by the ESC | **Unknown.** No current sensor on the FC |
| 5 V rail | PC5 | ADC1_INP8 | 10 kΩ / 10 kΩ, 100 nF | **V_5V = V_adc × 2.0** | 5.0 V → 2.5 V |

Resistors are 1 %, so expect up to about ±2 % divider error plus the VDDA tolerance. **Calibrate battery voltage against a multimeter** on each board.

For ArduPilot-style scaling (recommendation): voltage multiplier 11.0 on ADC pin 10; current pin 11 with amps-per-volt taken from the chosen ESC's datasheet; do not enable current monitoring until that value is known.

## Things firmware should know
- VBAT pin of the MCU is tied to 3V3: there is no backup battery, so RTC and backup registers reset at power-off.
- Source impedance of the VBAT divider is about 9.1 kΩ with a 100 nF reservoir: use a long ADC sampling time.
- The ESC current input has no divider. If an ESC outputs more than 3.3 V on its current pin, the pin (FT type) tolerates it but the reading saturates.
- Brown-out: the 5 V buck stops below about 5.3 V battery. On 2S, plan the low-voltage failsafe well above that.
