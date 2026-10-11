# AT070 enclosure

Parametric build123d model of a 3D-printed enclosure and desk stand for a 7" LCD
(InnoLux AT070TN92, 164.9 x 100 x 5.7 mm). Parts: front shell, snap-on lid, adjustable
tilting stand (base, cradle, strut), and fit-test coupons. Target printer: Bambu P1S
(256 mm bed), PLA, Bambu Studio.

The datasheet and mechanical drawing are in `docs/`.

## Design note: case centered on the visible area

The panel's active area (AA) is off-center on the panel outline. The case is centered
on the AA center (X -1.49, Y +2.26), not on the panel center, so the visible screen looks
centered in the case and the panel sits off-center inside it. The pocket is the smallest
rectangle centered on the AA center that holds the panel plus clearance (and the FPC
relief at the bottom). Locating blocks fill the larger gaps on the left and top walls so
the panel cannot shift.

## Build and test

    uv run pytest                  # geometry checks
    uv run python -m at070.build   # writes STEP, STL, 3MF per part and assembly.step to out/

All dimensions are named constants in `at070/params.py` (mm). Several are photo estimates
(driver board, HDMI socket, cable positions) and may need adjusting after measuring.

Coordinates (assembled): origin at the panel center on the glass face; +X right seen from
the front, +Y up (HDMI cable side), +Z toward the back. That frame is left-handed, so
`build.py` mirrors every part in X (`to_world`) before export; the exported parts are the
real, right-handed geometry. Keep `params.py` in front-view terms.

## Parts list (out/)

| File | Print orientation |
|---|---|
| `front_shell` | front face down, as modeled |
| `lid` | back face down, clips pointing up |
| `stand_base` | underside on the bed, as modeled (angle labels read from above, front toward you) |
| `stand_cradle` | upright, floor underside on the bed (pivot pins have a small flat at the bottom) |
| `stand_strut` | flat, upper face on the bed; the foot ridge points up |
| `coupon_fit_frame` | front face down; checks panel outline, window, FPC relief, and (full-height top-edge section) HDMI/power notches with the panel in place and one clip slot |
| `coupon_top_edge_lid` | back face down; snaps onto the fit frame's top-edge section to check the clip |

Suggested settings: 0.4 mm nozzle, 0.2 mm layers, 6 perimeters for the 2.4 mm walls
(wall count matters for the snap clips, so keep them solid), 15 to 20 % infill, no supports.
Print the coupons first.

`out/assembly.step` holds the shell, lid and reference mocks (panel, board keep-out, HDMI
plug, power cable) in assembled positions, one solid each, for visual checking. `out/stand_assembly.step` shows the stand at 15 degrees
with a case-sized box. The stand uses its own right-handed frame (X along the case edge, +Y
toward the back, Z up) and is not mirrored by `to_world`.

## Assembly

1. Place the panel face down in the front shell (the glass against the front plate).
2. Route the power cable into its notch in the top wall (lay it in from the back).
3. Press the lid on. The six hooks snap into the wall slots.
4. The HDMI plug goes in from outside through its notch in the top wall.
5. Assemble the stand: press the cradle's two side pins down into the sockets of the base
   towers (they snap in), and press the strut's top pin into the two sockets on the back of
   the cradle (open toward the back).
6. Set the case into the cradle on its bottom edge (landscape) or either side edge (portrait),
   never on the top edge, where the cables exit. It stands against the back rest.
7. Tilt: 0 (vertical) to 45 degrees in 5 degree steps. Lift the cradle back to the angle you
   want and click the strut's foot into the matching notch in the base rack; the angle is
   embossed beside each notch. For storage, swing the strut down flat against the cradle back.

Release: push each hook in through its wall slot with a small screwdriver and lift the lid.
