# RangerH743 sensor orientation

Status: derived from the hardware brief's axis table. Not checked on a
board. Confirm with a tilt test before any flight.

## Two separate rotations

ArduPilot applies two rotations, and this port keeps them apart on
purpose.

1. **Sensor to board frame.** Fixed in `hwdef.dat`. It depends only on
   how each chip is placed on the PCB.
2. **Board to aircraft frame.** The `AHRS_ORIENTATION` parameter. It
   depends on which board edge faces the nose. **This is not decided**,
   so the port does not set it.

## Board frame used by the firmware

Top side (MCU side) up:

- board +X = north edge (USB-C and CAN connectors)
- board +Y = east edge (companion and servo connectors)
- board +Z = down

This frame is a firmware convention chosen so the rotations below could
be written down. It is not a statement that the USB-C edge is the front
of the aircraft.

## Sensor to board rotations (in hwdef.dat)

| Sensor | +X | +Y | +Z | Board frame vector | hwdef rotation |
|---|---|---|---|---|---|
| ICM-42688-P | east | south | down | (-sy, sx, sz) | `ROTATION_YAW_90` |
| BMI088 | south | west | down | (-sx, -sy, sz) | `ROTATION_YAW_180` |

Both sets of axes are right-handed with Z down, so no roll or pitch flip
is needed even though the parts sit on the bottom side: the brief's axis
table already gives the directions as seen with the top side up.

## AHRS_ORIENTATION for each possible forward edge

Set this once the mechanical forward direction is fixed. Board mounted
flat, top side up.

| Board edge facing the nose | Connectors on that edge | `AHRS_ORIENTATION` |
|---|---|---|
| North | USB-C, CAN | 0 (None) |
| East | Companion, servos | 6 (Yaw270) |
| South | ESC, LiDAR | 4 (Yaw180) |
| West | TELEM1, RC | 2 (Yaw90) |

Worked example for the east edge: board +Y points at the nose and board
+X points to the aircraft's left, so a board vector (bx, by) becomes
(by, -bx) in the aircraft frame, which is a 270 degree yaw. Net effect
on the ICM-42688-P is Yaw90 then Yaw270 = no rotation, matching its +X
(east) pointing at the nose.

If the board is mounted upside down or at an angle, a different value
(or the custom orientation option) is needed and must be worked out
from the actual mount.

The external compass on the GPS connector has its own orientation
(`COMPASS_ORIENT`), set from how the GPS module is mounted.

## Tilt test (needs a board)

With the board in its airframe position and a ground station connected:

1. Level: accel Z reads about -9.8 m/s^2, roll and pitch about 0.
2. Nose down: pitch goes negative.
3. Right side down: roll goes positive.
4. Rotate clockwise seen from above: yaw increases.
5. If the BMI088 is fitted, both IMUs must agree in all four steps.

Any disagreement means a rotation above, or the brief's axis table, is
wrong. Fix it before flying.
