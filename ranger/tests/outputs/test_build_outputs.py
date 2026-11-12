"""Checks on the RangerH743 build outputs.

Run after ranger/scripts/build_fw.sh. These look at what the ArduPilot
build actually generated (hwdef.h, the DMA allocation, the firmware
images) rather than at the hwdef source.

A pass means the firmware was really compiled with the intended
configuration. It is not a hardware test.
"""
import base64
import json
import pathlib
import re
import zlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/RangerH743"

FLASH_KB = 2048
BOOTLOADER_KB = 128
STORAGE_KB = 2 * 128  # last two flash sectors hold parameters
BOARD_ID = 20743


@pytest.fixture(scope="module")
def hwdef_h():
    path = OUT / "hwdef.h"
    if not path.exists():
        pytest.fail("%s missing: run ranger/scripts/build_fw.sh first" % path)
    return path.read_text()


def define(text, name):
    m = re.search(r"^#define\s+%s\s+(.*?)\s*(?://.*)?$" % re.escape(name),
                  text, re.M)
    return None if m is None else m.group(1).strip()


def stream(text, name):
    v = define(text, name)
    assert v is not None, "%s not allocated" % name
    m = re.match(r"STM32_DMA_STREAM_ID\((\d), (\d)\)", v)
    assert m, v
    return int(m.group(1)), int(m.group(2))


def shared_streams(text):
    v = define(text, "SHARED_DMA_MASK") or ""
    return {(int(a), int(b)) for a, b in
            re.findall(r"STM32_DMA_STREAM_ID\((\d),(\d)\)", v)}


# ------------------------------------------------------ generated config

def test_clock_is_8mhz_hse(hwdef_h):
    assert define(hwdef_h, "STM32_HSECLK") == "8000000U"


def test_board_id(hwdef_h):
    assert define(hwdef_h, "APJ_BOARD_ID") == str(BOARD_ID)


def test_eight_pwm_outputs_in_two_timer_groups(hwdef_h):
    assert define(hwdef_h, "HAL_PWM_COUNT") == "8"
    assert define(hwdef_h, "HAL_PWM_GROUPS") == "HAL_PWM_GROUP1,HAL_PWM_GROUP2"


def test_eight_serial_ports(hwdef_h):
    assert define(hwdef_h, "HAL_UART_NUM_SERIAL_PORTS") == "8"
    assert "Empty::UARTDriver serial7Driver" not in hwdef_h
    assert "Empty::UARTDriver serial8Driver" in hwdef_h


def test_two_imu_probes_and_one_baro(hwdef_h):
    assert define(hwdef_h, "HAL_INS_PROBE_LIST") == "HAL_INS_PROBE1;HAL_INS_PROBE2"
    assert "AP_InertialSensor_Invensensev3::probe" in define(hwdef_h, "HAL_INS_PROBE1")
    assert "ROTATION_YAW_90" in define(hwdef_h, "HAL_INS_PROBE1")
    assert "AP_InertialSensor_BMI088::probe" in define(hwdef_h, "HAL_INS_PROBE2")
    assert "ROTATION_YAW_180" in define(hwdef_h, "HAL_INS_PROBE2")
    assert define(hwdef_h, "HAL_BARO_PROBE_LIST") == "HAL_BARO_PROBE1"
    baro = define(hwdef_h, "HAL_BARO_PROBE1")
    assert "AP_Baro_BMP388::probe" in baro
    assert "0x76" in baro or "118" in baro


def test_battery_defaults(hwdef_h):
    assert define(hwdef_h, "HAL_BATT_MONITOR_DEFAULT") == "3"
    assert define(hwdef_h, "HAL_BATT_VOLT_PIN") == "10"
    assert define(hwdef_h, "HAL_BATT_VOLT_SCALE") == "11.0"
    assert define(hwdef_h, "HAL_BATT_CURR_SCALE") is None
    assert define(hwdef_h, "HAL_BATT_CURR_PIN") is None


# ----------------------------------------------------------------- DMA

def test_motor_timer_has_a_dedicated_dma_stream(hwdef_h):
    """DShot on TIM1 needs TIM1_UP DMA; it must not be shared"""
    s = stream(hwdef_h, "STM32_TIM_TIM1_UP_DMA_STREAM")
    assert s not in shared_streams(hwdef_h)
    assert "HAL_PWM1_DMA_CONFIG true" in hwdef_h


def test_primary_imu_spi_dma_is_not_shared(hwdef_h):
    shared = shared_streams(hwdef_h)
    assert stream(hwdef_h, "STM32_SPI_SPI1_RX_DMA_STREAM") not in shared
    assert stream(hwdef_h, "STM32_SPI_SPI1_TX_DMA_STREAM") not in shared


def test_no_two_unshared_requests_on_one_stream(hwdef_h):
    used = {}
    for name, a, b, comment in re.findall(
            r"^#define\s+(STM32_\w+_DMA_STREAM)\s+STM32_DMA_STREAM_ID\((\d), (\d)\)(.*)$",
            hwdef_h, re.M):
        used.setdefault((int(a), int(b)), []).append((name, comment))
    assert len(used) <= 16
    for key, users in used.items():
        if len(users) > 1:
            assert key in shared_streams(hwdef_h), users
            assert all("shared" in c for _, c in users), users


def test_high_rate_links_have_dma(hwdef_h):
    for port in ("USART1", "USART2", "USART3", "UART4"):
        for d in ("RX", "TX"):
            stream(hwdef_h, "STM32_UART_%s_%s_DMA_STREAM" % (port, d))


# ------------------------------------------------------------- images

def test_firmware_images_exist():
    for name in ("arducopter.apj", "arducopter.bin", "RangerH743_bl.bin",
                 "SHA256SUMS", "build.log"):
        assert (OUT / name).stat().st_size > 0, name


def test_apj_is_for_this_board_and_fits_flash():
    apj = json.loads((OUT / "arducopter.apj").read_text())
    assert apj["board_id"] == BOARD_ID
    image = zlib.decompress(base64.b64decode(apj["image"]))
    assert len(image) == apj["image_size"]
    assert image == (OUT / "arducopter.bin").read_bytes()
    limit = (FLASH_KB - BOOTLOADER_KB - STORAGE_KB) * 1024
    assert 100 * 1024 < len(image) <= limit, (
        "firmware is %u bytes, limit %u" % (len(image), limit))


def test_bootloader_fits_first_sector():
    size = (OUT / "RangerH743_bl.bin").stat().st_size
    assert 0 < size <= BOOTLOADER_KB * 1024


def test_firmware_vector_table_points_into_application_flash():
    """initial SP in RAM, reset vector inside the app region at 0x08020000"""
    b = (OUT / "arducopter.bin").read_bytes()
    sp = int.from_bytes(b[0:4], "little")
    reset = int.from_bytes(b[4:8], "little")
    app_start = 0x08000000 + BOOTLOADER_KB * 1024
    assert 0x20000000 <= sp <= 0x38010000, hex(sp)
    assert app_start < reset < 0x08000000 + FLASH_KB * 1024, hex(reset)
    assert reset & 1, "reset vector must be a Thumb address"
