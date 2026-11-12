# Boot, Debug and Recovery (AS-DESIGNED)

## Hardware
| Item | Design |
|---|---|
| Clock | HSE **8.000 MHz** crystal (3225, CL 10 pF, part not yet selected) on PH0/PH1, 12 pF load caps. No 32.768 kHz crystal: use LSI for RTC/IWDG |
| Reset | NRST: 100 nF to GND, internal pull-up, wired to SWD pin 10. **No reset button** |
| BOOT0 | 10 kΩ pull-down. **SW1** pulls it to 3.3 V. Sampled at reset |
| SWD | J_SWD1, ARM 10-pin 1.27 mm: 1 VTref (3V3), 2 SWDIO (PA13), 3 GND, 4 SWCLK (PA14), 5 GND, 6 SWO (PB3), 7 key, 8 NC, 9 GND, 10 NRST. On the **bottom** side |
| USB | USB-C receptacle J_USB1, device only. D− = PA11, D+ = PA12, through USBLC6-2SC6 ESD. CC1 and CC2 each 5.1 kΩ to GND |
| VBUS sense | PA9 as GPIO input through 10 k / 20 k (3.33 V when plugged). Not the OTG VBUS alternate function |
| Debug UART | UART7 on test pads TP1 (TX, PE8) and TP2 (RX, PE7) on the bottom. No connector |
| LEDs | Active low: red PB2, green PD7, blue PE15 |

## Bootloader assumptions (not yet proven on hardware)
- ST's ROM bootloader is entered with BOOT0 high at reset. The H743 ROM is documented by ST (AN2606) to offer USB DFU on PA11/PA12; **AN2606 was not re-read for this project**, including its HSE-frequency requirements for USB. Treat DFU as *expected*, to be confirmed on the first board.
- The board powers the MCU from USB alone, so DFU does not need a battery.
- There is no reset button: to enter the ROM bootloader, hold SW1 while plugging in USB (power-on reset).
- An ArduPilot-style bootloader would occupy the first flash sector; reserve it in the board definition if used.

## Recommended first flash (prototype)
1. Current-limited bench supply, no peripherals. Check 5 V, 3.3 V and 3V3_SENS before connecting a probe.
2. Connect an ST-LINK or J-Link to J_SWD1. Read the device ID. This proves MCU power, VCAP and SWD independent of the crystal and USB.
3. Flash a minimal blink that starts the HSE and toggles the three LEDs.
4. Flash the bootloader over SWD, then try USB.
5. Separately test ROM DFU (hold SW1, plug USB) so a recovery path is known to work.

## Recovery
- SWD always works if the MCU is powered and firmware has not disabled PA13/PA14. Do not remap those pins.
- If firmware disables SWD, hold SW1 during power-up: the ROM bootloader leaves SWD enabled.
- Connect-under-reset is available because NRST is on the SWD header.
