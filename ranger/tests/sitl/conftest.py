"""SITL fixture for the Ranger tests.

Starts the ArduCopter SITL binary directly (no MAVProxy, no GUI), loads
the stock copter SITL defaults plus the RangerH743 board defaults, and
hands the tests a small MAVLink helper.

SITL exercises ArduPilot's flight logic against simulated sensors. It
does not run the RangerH743 hwdef, pins, DMA or drivers, so nothing here
is evidence about the Ranger FC electronics.
"""
import os
import pathlib
import shutil
import subprocess
import time

import pytest
from pymavlink import mavutil

ROOT = pathlib.Path(__file__).resolve().parents[3]
SITL_BIN = pathlib.Path(os.environ.get(
    "RANGER_SITL_BIN", ROOT / "build/sitl/bin/arducopter"))
SITL_DEFAULTS = [
    ROOT / "Tools/autotest/default_params/copter.parm",
    ROOT / "libraries/AP_HAL_ChibiOS/hwdef/RangerH743/defaults.parm",
    ROOT / "ranger/sitl/ranger_sitl.parm",
]
SPEEDUP = os.environ.get("RANGER_SITL_SPEEDUP", "5")
PORT = 5760


class Vehicle:
    """thin MAVLink helper that keeps a GCS heartbeat going"""

    def __init__(self, conn):
        self.conn = conn
        self.mav = conn.mav
        self.last_hb = 0.0
        self.statustexts = []

    # -- plumbing ---------------------------------------------------
    def pump(self):
        now = time.time()
        if now - self.last_hb > 0.2:
            self.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
            self.last_hb = now

    def recv(self, types, timeout=30, condition=None):
        """wait (wall clock) for a message of the given type(s)"""
        if isinstance(types, str):
            types = [types]
        want = set(types) | {"STATUSTEXT"}
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.pump()
            m = self.conn.recv_match(type=list(want), blocking=True, timeout=0.2)
            if m is None:
                continue
            if m.get_type() == "STATUSTEXT":
                self.statustexts.append(m.text)
                if "STATUSTEXT" not in types:
                    continue
            if condition is None or condition(m):
                return m
        return None

    def wait_until(self, fn, timeout=60):
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.recv("HEARTBEAT", timeout=0.3)
            if fn():
                return True
        return False

    # -- parameters -------------------------------------------------
    def get_param(self, name, timeout=15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.mav.param_request_read_send(
                self.conn.target_system, self.conn.target_component,
                name.encode(), -1)
            m = self.recv("PARAM_VALUE", timeout=2,
                          condition=lambda m: m.param_id == name)
            if m is not None:
                return m.param_value
        raise AssertionError("no PARAM_VALUE for %s" % name)

    def set_param(self, name, value, timeout=15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.mav.param_set_send(
                self.conn.target_system, self.conn.target_component,
                name.encode(), float(value),
                mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
            m = self.recv("PARAM_VALUE", timeout=2,
                          condition=lambda m: m.param_id == name)
            if m is not None and abs(m.param_value - float(value)) < 1e-4:
                return
        raise AssertionError("could not set %s=%s" % (name, value))

    # -- commands ---------------------------------------------------
    def command(self, cmd, *params, timeout=10):
        p = list(params) + [0] * (7 - len(params))
        self.mav.command_long_send(
            self.conn.target_system, self.conn.target_component, cmd, 0, *p)
        ack = self.recv("COMMAND_ACK", timeout=timeout,
                        condition=lambda m: m.command == cmd)
        return None if ack is None else ack.result

    def arm(self):
        return self.command(
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 1)

    def disarm(self, force=False):
        return self.command(
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
            21196 if force else 0)

    def heartbeat(self, timeout=10):
        return self.recv(
            "HEARTBEAT", timeout=timeout,
            condition=lambda m: m.get_srcComponent() == 1 and
            m.type != mavutil.mavlink.MAV_TYPE_GCS)

    def armed(self):
        hb = self.heartbeat()
        assert hb is not None, "vehicle heartbeat lost"
        return bool(hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

    def mode(self):
        hb = self.heartbeat()
        assert hb is not None, "vehicle heartbeat lost"
        return mavutil.mode_string_v10(hb)

    def set_mode(self, name, timeout=20):
        mode_id = self.conn.mode_mapping()[name]
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.conn.set_mode(mode_id)
            if self.mode() == name:
                return True
        return False

    def wait_mode(self, name, timeout=60):
        return self.wait_until(lambda: self.mode() == name, timeout)


@pytest.fixture(scope="session")
def vehicle(tmp_path_factory):
    if not SITL_BIN.exists():
        pytest.fail("SITL binary not found at %s. Build it with "
                    "ranger/scripts/build_sitl.sh" % SITL_BIN)
    for f in SITL_DEFAULTS:
        assert f.exists(), f
    workdir = tmp_path_factory.mktemp("sitl")
    log = open(workdir / "sitl_stdout.log", "w")
    proc = subprocess.Popen(
        [str(SITL_BIN), "--model", "+", "--speedup", SPEEDUP, "-w", "-I0",
         "--defaults", ",".join(str(f) for f in SITL_DEFAULTS),
         "--sim-address=127.0.0.1"],
        cwd=workdir, stdout=log, stderr=subprocess.STDOUT)
    conn = None
    try:
        deadline = time.time() + 60
        while conn is None and time.time() < deadline:
            assert proc.poll() is None, "SITL exited early, see %s" % log.name
            try:
                conn = mavutil.mavlink_connection(
                    "tcp:127.0.0.1:%u" % PORT, source_system=255,
                    autoreconnect=False)
            except OSError:
                time.sleep(0.5)
        assert conn is not None, "could not connect to SITL"
        v = Vehicle(conn)
        hb = None
        deadline = time.time() + 60
        while hb is None and time.time() < deadline:
            v.pump()
            hb = conn.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        assert hb is not None, "no heartbeat from SITL"
        conn.target_system = hb.get_srcSystem()
        conn.target_component = hb.get_srcComponent()
        v.first_heartbeat = hb
        v.workdir = workdir
        v.mav.request_data_stream_send(
            conn.target_system, conn.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
        yield v
    finally:
        if conn is not None:
            conn.close()
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        keep = os.environ.get("RANGER_SITL_ARTIFACTS")
        if keep:
            dest = pathlib.Path(keep)
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy(workdir / "sitl_stdout.log", dest / "sitl_stdout.log")
            for b in (workdir / "logs").glob("*.BIN"):
                shutil.copy(b, dest / b.name)
