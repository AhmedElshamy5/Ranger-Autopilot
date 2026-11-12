"""Software-in-the-loop tests for the Ranger ArduCopter configuration.

Tests run in file order and share one simulated vehicle.

Scope: MAVLink link, parameters, the RangerH743 failsafe and logging
defaults, arming checks, a guided flight and a battery failsafe, all in
simulation. Not in scope: anything about the real board.
"""
import time

from pymavlink import mavutil

M = mavutil.mavlink


def test_heartbeat(vehicle):
    hb = vehicle.first_heartbeat
    assert hb.autopilot == M.MAV_AUTOPILOT_ARDUPILOTMEGA
    assert hb.type == M.MAV_TYPE_QUADROTOR
    assert not hb.base_mode & M.MAV_MODE_FLAG_SAFETY_ARMED


def test_firmware_version_is_reported(vehicle):
    vehicle.mav.command_long_send(
        vehicle.conn.target_system, vehicle.conn.target_component,
        M.MAV_CMD_REQUEST_MESSAGE, 0,
        M.MAVLINK_MSG_ID_AUTOPILOT_VERSION, 0, 0, 0, 0, 0, 0)
    m = vehicle.recv("AUTOPILOT_VERSION", timeout=15)
    assert m is not None
    major = (m.flight_sw_version >> 24) & 0xFF
    minor = (m.flight_sw_version >> 16) & 0xFF
    assert (major, minor) == (4, 7), "unexpected baseline %u.%u" % (major, minor)


def test_parameter_read_write_roundtrip(vehicle):
    original = vehicle.get_param("RTL_ALT")
    try:
        vehicle.set_param("RTL_ALT", original + 250)
        assert vehicle.get_param("RTL_ALT") == original + 250
    finally:
        vehicle.set_param("RTL_ALT", original)
    assert vehicle.get_param("RTL_ALT") == original


def test_ranger_failsafe_defaults_are_loaded(vehicle):
    """values come from hwdef/RangerH743/defaults.parm"""
    assert vehicle.get_param("FS_THR_ENABLE") == 1
    assert vehicle.get_param("FS_GCS_ENABLE") == 1
    assert vehicle.get_param("FS_EKF_ACTION") == 1


def test_ranger_logging_defaults_are_loaded(vehicle):
    assert vehicle.get_param("LOG_BACKEND_TYPE") == 1
    assert vehicle.get_param("LOG_DISARMED") == 0


def test_simulated_sensors_present_and_healthy(vehicle):
    need = (M.MAV_SYS_STATUS_SENSOR_3D_GYRO |
            M.MAV_SYS_STATUS_SENSOR_3D_ACCEL |
            M.MAV_SYS_STATUS_SENSOR_ABSOLUTE_PRESSURE)
    ok = vehicle.recv(
        "SYS_STATUS", timeout=90,
        condition=lambda m: (m.onboard_control_sensors_present & need) == need
        and (m.onboard_control_sensors_health & need) == need)
    assert ok is not None, "gyro/accel/baro not healthy in SITL"


def test_prearm_check_blocks_arming(vehicle):
    """a failing pre-arm check must refuse the arm command"""
    assert vehicle.set_mode("GUIDED")
    vehicle.set_param("BATT_ARM_VOLT", 99)
    try:
        time.sleep(1)
        result = vehicle.arm()
        assert result is not None, "no COMMAND_ACK for arm"
        assert result != M.MAV_RESULT_ACCEPTED
        assert not vehicle.armed()
    finally:
        vehicle.set_param("BATT_ARM_VOLT", 0)


def test_arms_in_guided_when_checks_pass(vehicle):
    assert vehicle.set_mode("GUIDED")
    deadline = time.time() + 180
    result = None
    while time.time() < deadline:
        result = vehicle.arm()
        if result == M.MAV_RESULT_ACCEPTED:
            break
        time.sleep(2)
    assert result == M.MAV_RESULT_ACCEPTED, (
        "never armed; last messages: %s" % vehicle.statustexts[-5:])
    assert vehicle.wait_until(vehicle.armed, timeout=10)


def test_guided_takeoff_and_position_target(vehicle):
    assert vehicle.armed(), "previous test should have left the vehicle armed"
    result = vehicle.command(M.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 5)
    assert result == M.MAV_RESULT_ACCEPTED
    climbed = vehicle.recv(
        "GLOBAL_POSITION_INT", timeout=60,
        condition=lambda m: m.relative_alt > 4000)
    assert climbed is not None, "did not reach 4 m"

    start = vehicle.recv("LOCAL_POSITION_NED", timeout=10)
    assert start is not None
    target_x = start.x + 10
    mask = (M.POSITION_TARGET_TYPEMASK_VX_IGNORE |
            M.POSITION_TARGET_TYPEMASK_VY_IGNORE |
            M.POSITION_TARGET_TYPEMASK_VZ_IGNORE |
            M.POSITION_TARGET_TYPEMASK_AX_IGNORE |
            M.POSITION_TARGET_TYPEMASK_AY_IGNORE |
            M.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
            M.POSITION_TARGET_TYPEMASK_YAW_IGNORE |
            M.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE)
    vehicle.mav.set_position_target_local_ned_send(
        0, vehicle.conn.target_system, vehicle.conn.target_component,
        M.MAV_FRAME_LOCAL_NED, mask,
        target_x, start.y, -5, 0, 0, 0, 0, 0, 0, 0, 0)
    arrived = vehicle.recv(
        "LOCAL_POSITION_NED", timeout=60,
        condition=lambda m: abs(m.x - target_x) < 1.5)
    assert arrived is not None, "did not fly to the guided position target"
    assert vehicle.mode() == "GUIDED"


def test_battery_failsafe_lands_the_vehicle(vehicle):
    assert vehicle.armed()
    vehicle.set_param("BATT_LOW_VOLT", 10.5)
    vehicle.set_param("BATT_FS_LOW_ACT", 1)  # land
    vehicle.set_param("SIM_BATT_VOLTAGE", 10.0)
    try:
        assert vehicle.wait_mode("LAND", timeout=60), (
            "battery failsafe did not switch to LAND (mode %s)" % vehicle.mode())
        assert vehicle.wait_until(lambda: not vehicle.armed(), timeout=120), (
            "vehicle did not land and disarm")
    finally:
        if vehicle.armed():
            vehicle.disarm(force=True)
        vehicle.set_param("SIM_BATT_VOLTAGE", 12.6)
        vehicle.set_param("BATT_FS_LOW_ACT", 0)
        vehicle.set_param("BATT_LOW_VOLT", 0)


def test_flight_log_was_written(vehicle):
    vehicle.mav.log_request_list_send(
        vehicle.conn.target_system, vehicle.conn.target_component, 0, 0xFFFF)
    entry = vehicle.recv("LOG_ENTRY", timeout=20)
    assert entry is not None, "no LOG_ENTRY reply"
    assert entry.num_logs >= 1
    assert entry.size > 0
    assert list((vehicle.workdir / "logs").glob("*.BIN")), "no .BIN on disk"
