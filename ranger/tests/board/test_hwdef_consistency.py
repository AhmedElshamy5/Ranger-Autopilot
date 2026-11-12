"""Board-definition consistency checks for RangerH743.

These run without a build and without hardware. They compare
hwdef.dat against ranger/hardware/pinmap.csv (the transcription of the
hardware brief) and against the upstream STM32H743 alternate-function
table, and they pin down the decisions that must stay provisional.

They prove the board definition matches the documented design. They do
not prove the design, or any PCB, works.
"""
import csv
import importlib.util
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
HWDEF_DIR = ROOT / "libraries/AP_HAL_ChibiOS/hwdef/RangerH743"
HWDEF = HWDEF_DIR / "hwdef.dat"
HWDEF_BL = HWDEF_DIR / "hwdef-bl.dat"
DEFAULTS = HWDEF_DIR / "defaults.parm"
PINMAP = ROOT / "ranger/hardware/pinmap.csv"
AF_TABLE = ROOT / "libraries/AP_HAL_ChibiOS/hwdef/scripts/STM32H743xx.py"
BOARD_TYPES = ROOT / "Tools/AP_Bootloader/board_types.txt"

HANDOFF = ROOT / "ranger/hardware/handoff"

PIN_RE = re.compile(r"^P[A-K]\d{1,2}$")

# pins the brief lists as not connected on the A0.1 board
UNCONNECTED = {"PA2", "PA15", "PB0", "PB1", "PB4", "PC2", "PC3",
               "PC14", "PC15", "PE1"}
# pins that exist on the LQFP-100 package (ports A-E 0..15, PH0/PH1)
LQFP100_PORTS = "ABCDE"


def strip_comment(line):
    return line.split("#", 1)[0].strip()


def parse_hwdef(path):
    """return (pins, directives): pins maps pin -> (label, type, extras)"""
    pins = {}
    directives = []
    for raw in path.read_text().splitlines():
        line = strip_comment(raw)
        if not line:
            continue
        parts = line.split()
        if PIN_RE.match(parts[0]):
            assert parts[0] not in pins, "pin %s defined twice in %s" % (
                parts[0], path.name)
            pins[parts[0]] = (parts[1], parts[2], parts[3:])
        else:
            directives.append(parts)
    return pins, directives


def load_pinmap():
    with PINMAP.open(newline="") as f:
        return {row["pin"]: row for row in csv.DictReader(f)}


def load_af_table():
    spec = importlib.util.spec_from_file_location("STM32H743xx", AF_TABLE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.AltFunction_map


@pytest.fixture(scope="module")
def hwdef():
    return parse_hwdef(HWDEF)


@pytest.fixture(scope="module")
def pinmap():
    return load_pinmap()


def directive(directives, name):
    return [d for d in directives if d[0] == name]


def defines(directives):
    return {d[1]: " ".join(d[2:]) for d in directives if d[0] == "define"}


# ------------------------------------------------------------ pin map

def test_every_hwdef_pin_is_in_the_pinmap(hwdef, pinmap):
    pins, _ = hwdef
    assert set(pins) == set(pinmap), (
        "hwdef.dat and pinmap.csv disagree on which pins are used: "
        "only in hwdef %s, only in pinmap %s" % (
            sorted(set(pins) - set(pinmap)), sorted(set(pinmap) - set(pins))))


def test_labels_and_types_match_the_pinmap(hwdef, pinmap):
    pins, _ = hwdef
    for pin, (label, ptype, _) in pins.items():
        row = pinmap[pin]
        assert label == row["hwdef_label"], pin
        assert ptype == row["hwdef_type"], pin


def test_no_unconnected_pin_is_used(hwdef):
    pins, _ = hwdef
    assert not (set(pins) & UNCONNECTED)


def test_all_pins_exist_on_lqfp100(hwdef):
    pins, _ = hwdef
    for pin in pins:
        assert pin[1] in LQFP100_PORTS, "%s is not on the LQFP-100" % pin


def test_alternate_functions_match_upstream_h743_table(hwdef, pinmap):
    """the AF number in the brief must be the one the MCU really has"""
    af_map = load_af_table()
    pins, _ = hwdef
    checked = 0
    for pin, (label, ptype, _) in pins.items():
        want = pinmap[pin]["af"]
        if want == "":
            continue
        key = "%s:%s" % (pin, label)
        assert key in af_map, "%s is not an alternate function of the H743" % key
        assert af_map[key] == int(want), key
        checked += 1
    assert checked >= 45


# ----------------------------------------------- hardware handoff CSV

def load_handoff_pins():
    with (HANDOFF / "MCU_PINOUT.csv").open(newline="", encoding="utf-8-sig") as f:
        return {r["GPIO"]: r for r in csv.DictReader(f) if r["GPIO"]}


def test_pinmap_agrees_with_handoff_mcu_pinout(pinmap):
    """every pin the firmware uses must match the netlist-generated CSV"""
    handoff = load_handoff_pins()
    rename = {"FDCAN1_RX": "CAN1_RX", "FDCAN1_TX": "CAN1_TX"}
    for pin, row in pinmap.items():
        assert pin in handoff, "%s not in MCU_PINOUT.csv" % pin
        h = handoff[pin]
        assert h["Net"], "%s has no net in the handoff" % pin
        assert "UNUSED" not in h["Firmware purpose"], pin
        if row["af"] and row["hwdef_type"] != "SWD":
            assert h["Alternate function"] == "AF" + row["af"], pin
            func = rename.get(h["Peripheral / function"], h["Peripheral / function"])
            assert func == row["hwdef_label"], pin
        if row["hwdef_type"] == "ADC1":
            assert h["Alternate function"] == "analog", pin


def test_handoff_has_no_connected_pin_missing_from_hwdef(hwdef):
    """a net on an MCU GPIO that the firmware ignores is a mistake"""
    pins, _ = hwdef
    # crystal and SWO are handled by the clock config / left at reset state
    ignore = {"PH0", "PH1", "PB3"}
    for pin, h in load_handoff_pins().items():
        key = pin.replace("_C", "")
        if h["Net"] and key not in ignore:
            assert key in pins, "%s (%s) is connected but not in hwdef.dat" % (
                pin, h["Net"])
        if not h["Net"]:
            assert key in UNCONNECTED, pin
            assert key not in pins, pin


def test_adc_channels_and_scales_match_handoff(hwdef):
    pins, d = hwdef
    handoff = load_handoff_pins()
    assert handoff["PC0"]["Peripheral / function"] == "ADC1_INP10"
    assert handoff["PC1"]["Peripheral / function"] == "ADC1_INP11"
    assert handoff["PC5"]["Peripheral / function"] == "ADC1_INP8"
    assert "100k/10k" in handoff["PC0"]["Pull / series"]
    assert "10k/10k" in handoff["PC5"]["Pull / series"]
    assert "SCALE(2)" in pins["PC5"][2]
    assert "SCALE(1)" in pins["PC0"][2]


# ------------------------------------------------------------- basics

def test_mcu_clock_and_flash(hwdef):
    _, d = hwdef
    assert directive(d, "MCU") == [["MCU", "STM32H7xx", "STM32H743xx"]]
    assert directive(d, "OSCILLATOR_HZ") == [["OSCILLATOR_HZ", "8000000"]]
    assert directive(d, "FLASH_SIZE_KB") == [["FLASH_SIZE_KB", "2048"]]
    assert directive(d, "FLASH_RESERVE_START_KB") == [
        ["FLASH_RESERVE_START_KB", "128"]]


def test_board_id_is_named_and_outside_upstream_range(hwdef):
    _, d = hwdef
    assert directive(d, "APJ_BOARD_ID") == [["APJ_BOARD_ID", "AP_HW_RANGERH743"]]
    ids = {}
    for line in BOARD_TYPES.read_text().splitlines():
        m = re.match(r"([-\w]+)\s+(\d+)\s*$", strip_comment(line))
        if m:
            ids.setdefault(int(m.group(2)), []).append(m.group(1))
    ours = [k for k, v in ids.items() if "AP_HW_RANGERH743" in v]
    assert len(ours) == 1
    # 1000-19999 is reserved for IDs allocated by ArduPilot upstream
    assert ours[0] > 19999
    assert ids[ours[0]] == ["AP_HW_RANGERH743"], "board ID collision"


def test_bootloader_matches_main_definition(hwdef):
    _, d = hwdef
    bl_pins, bl_d = parse_hwdef(HWDEF_BL)
    for name in ("MCU", "APJ_BOARD_ID", "OSCILLATOR_HZ", "FLASH_SIZE_KB"):
        assert directive(bl_d, name) == directive(d, name), name
    main_pins, _ = hwdef
    main_start = int(directive(d, "FLASH_RESERVE_START_KB")[0][1])
    assert int(directive(bl_d, "FLASH_BOOTLOADER_LOAD_KB")[0][1]) == main_start
    for pin, (label, ptype, _) in bl_pins.items():
        if label.startswith("LED_"):
            assert main_pins[pin][0].startswith("LED_"), pin
            continue
        assert main_pins[pin][:2] == (label, ptype), pin


# ------------------------------------------------------------ serials

def test_serial_order_is_the_documented_mapping(hwdef):
    _, d = hwdef
    assert directive(d, "SERIAL_ORDER")[0][1:] == [
        "OTG1", "USART2", "USART3", "UART4", "USART6", "USART1",
        "UART7", "UART8"]
    defs = defines(d)
    assert defs["DEFAULT_SERIAL4_PROTOCOL"] == "SerialProtocol_Rangefinder"
    assert defs["DEFAULT_SERIAL5_PROTOCOL"] == "SerialProtocol_RCIN"
    assert defs["DEFAULT_SERIAL6_PROTOCOL"] == "SerialProtocol_None"
    assert defs["DEFAULT_SERIAL7_PROTOCOL"] == "SerialProtocol_None"


def test_serial_order_matches_handoff_suggestion(hwdef):
    _, d = hwdef
    order = directive(d, "SERIAL_ORDER")[0][1:]
    with (HANDOFF / "UART_PORT_MAP.csv").open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 7
    for row in rows:
        name = [v for k, v in row.items() if k.startswith("Suggested ArduPilot")][0]
        assert order[int(name.replace("SERIAL", ""))] == row["UART instance"]


def test_uart8_is_receive_only(hwdef):
    pins, _ = hwdef
    labels = {v[0] for v in pins.values()}
    assert "UART8_RX" in labels
    assert "UART8_TX" not in labels


# ------------------------------------------------------------ sensors

def test_imu_order_and_board_frame_rotations(hwdef):
    _, d = hwdef
    imus = directive(d, "IMU")
    assert imus == [
        ["IMU", "Invensensev3", "SPI:icm42688", "ROTATION_YAW_90"],
        ["IMU", "BMI088", "SPI:bmi088_a", "SPI:bmi088_g", "ROTATION_YAW_180"],
    ]


def test_spi_devices_respect_datasheet_clock_limits(hwdef):
    _, d = hwdef
    limits = {"icm42688": 24, "bmi088_a": 10, "bmi088_g": 10,
              "pixartflow": 2}
    buses = {"icm42688": "SPI1", "bmi088_a": "SPI2", "bmi088_g": "SPI2",
             "pixartflow": "SPI4"}
    cs = {"icm42688": "ICM42688_CS", "bmi088_a": "BMI088_A_CS",
          "bmi088_g": "BMI088_G_CS", "pixartflow": "FLOW_CS"}
    devs = {x[1]: x for x in directive(d, "SPIDEV")}
    assert set(devs) == set(limits), "unexpected SPI device declared"
    for name, dev in devs.items():
        assert dev[2] == buses[name]
        assert dev[4] == cs[name]
        for speed in dev[6:8]:
            assert int(speed.replace("*MHZ", "")) <= limits[name], name


def test_baro_is_bmp390_on_internal_bus(hwdef):
    _, d = hwdef
    assert directive(d, "BARO") == [["BARO", "BMP388", "I2C:0:0x76"]]
    assert directive(d, "I2C_ORDER") == [["I2C_ORDER", "I2C2", "I2C1"]]
    assert defines(d)["HAL_I2C_INTERNAL_MASK"] == "1"


# ------------------------------------------------------------ outputs

def test_pwm_outputs(hwdef):
    pins, _ = hwdef
    expect = {
        "PE9": ("TIM1_CH1", 1), "PE11": ("TIM1_CH2", 2),
        "PE13": ("TIM1_CH3", 3), "PE14": ("TIM1_CH4", 4),
        "PD12": ("TIM4_CH1", 5), "PD13": ("TIM4_CH2", 6),
        "PD14": ("TIM4_CH3", 7), "PD15": ("TIM4_CH4", 8),
    }
    found = {}
    for pin, (label, _, extra) in pins.items():
        for e in extra:
            m = re.match(r"PWM\((\d+)\)", e)
            if m:
                found[pin] = (label, int(m.group(1)))
    assert found == expect


def test_leds_idle_off_and_active_low(hwdef):
    pins, d = hwdef
    for pin in ("PB2", "PD7", "PE15"):
        assert "HIGH" in pins[pin][2], "%s must idle high (LED off)" % pin
    assert "HAL_GPIO_LED_ON" not in defines(d), "default (0, active low) expected"


def test_sensor_rail_on_and_can_enabled_at_boot(hwdef):
    pins, _ = hwdef
    assert "HIGH" in pins["PB12"][2]
    assert "LOW" in pins["PC13"][2]


# -------------------------------------------- provisional must stay so

def test_battery_monitor_is_voltage_only(hwdef):
    _, d = hwdef
    defs = defines(d)
    assert defs["HAL_BATT_MONITOR_DEFAULT"] == "3"
    assert defs["HAL_BATT_VOLT_PIN"] == "10"
    assert defs["HAL_BATT_CURR_PIN"] == "11"
    assert float(defs["HAL_BATT_VOLT_SCALE"]) == 11.0
    assert "HAL_BATT_CURR_SCALE" not in defs, (
        "no current sensor on the FC: do not invent a current scale")


def test_flow_sensor_is_not_enabled_by_default(hwdef):
    """the PMW3901 device is declared, but nothing may switch it on"""
    _, d = hwdef
    assert not directive(d, "OPTFLOW")
    assert not [k for k in defines(d) if "OPTFLOW" in k or "FLOW_TYPE" in k]


def test_defaults_do_not_decide_open_hardware_questions():
    forbidden = ("FRAME_CLASS", "FRAME_TYPE", "AHRS_ORIENTATION",
                 "MOT_PWM_TYPE", "SERVO_BLH", "SERVO_DSHOT",
                 "BATT_AMP", "BATT_CURR", "BATT_MONITOR", "BATT_VOLT_MULT",
                 "INS_", "RNGFND", "FLOW_")
    for raw in DEFAULTS.read_text().splitlines():
        line = strip_comment(raw)
        if not line:
            continue
        name = line.split()[0]
        for bad in forbidden:
            assert not name.startswith(bad), (
                "%s would turn a provisional hardware decision into a "
                "firmware default" % name)
        m = re.match(r"SERVO(\d+)_FUNCTION", name)
        assert m is None, "no motor/servo function mapping in board defaults"
