# AT070 enclosure

Parametric build123d model of a 3D-printed enclosure with a built-in kickstand for a 7" LCD
(InnoLux AT070TN92, 164.9 x 100 x 5.7 mm). Parts: front shell, snap-on lid, kickstand (main
flap, portrait prop, hinge blocks), and fit-test coupons. Target printer: Bambu P1S
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
| `kickstand_flap` | flat, plate underside on the bed (the knuckle and cam rise above it); a teardrop blind hole in each knuckle end, point up, prints without droop |
| `kickstand_prop` | same, flat |
| `hinge_block` | standing on its outer end face (hinge axis vertical, pin up): every layer has the same profile, so no supports, and the pin prints round. Print 2 |
| `hinge_block_spring` | same, pin and detent leaf both grow straight up. Print 2 |
| `coupon_fit_frame` | front face down; checks panel outline, window, FPC relief, and (full-height top-edge section) HDMI/power notches with the panel in place and one clip slot |
| `coupon_top_edge_lid` | back face down; snaps onto the fit frame's top-edge section to check the clip |
| `coupon_hinge_lid` | back face down; 50 x 40 piece of lid plate with the four slots of both blocks |
| `coupon_hinge_flap` | flat; 25 wide plate, knuckle with cam and a hole at each end; use with one `hinge_block` and one `hinge_block_spring` |

Suggested settings: 0.4 mm nozzle, 0.2 mm layers, 6 perimeters for the 2.4 mm walls
(wall count matters for the snap clips, so keep them solid), 15 to 20 % infill, no supports.
Print the coupons first. The hinge coupon (`coupon_hinge_lid`, `coupon_hinge_flap`, one `hinge_block` and one
`hinge_block_spring`) checks the snap fit, the pin fit and the clicks.

`out/assembly.step` holds the shell, lid and reference mocks (panel, board keep-out, HDMI
plug, power cable) in assembled positions, one solid each, for visual checking.
`out/kickstand_assembly.step` shows the shell and lid with all four hinge blocks, the prop
closed and the main flap open at the notch nearest 30 degrees of tilt.

Print 4 hinge blocks in total: 2 `hinge_block` and 2 `hinge_block_spring`. Each flap uses one
of each. The same block fits both flaps.

## Kickstand

Nothing protrudes from the lid back, so the lid still prints back face down without supports.
The lid has eight through-slots (two per hinge block). A hinge block sits on the lid back; it has a
pair of snap legs on each side of the hinge axis, each pair through its own slot, and the barbs
catch the lid underside (snaps in once, meant to stay). Holding the block down on both sides of the
axis keeps it from lifting when the flap is pushed.
The hinge line is 8 mm tall (8 mm knuckle). Each block has a 4 mm pin on its inner face that enters a blind hole in the flap's knuckle end
(4.4 mm hole, 4 mm engagement), and, on the spring
variant, a leaf spring whose rounded tip clicks into steep-flanked V notches (60 degree flanks) on the flap's cam.
`kickstand.detent_table()` estimates the detent holding torque against the case weight (3.5 N assumed).

The kickstand parts are modeled in the case's model frame (and a canonical hinge frame, see
`at070/kickstand.py`); `build.py` mirrors them like the lid.

- **Main flap (landscape):** 120 wide, hinge 60 above the bottom edge, 56 from hinge to free
  end. Clicks at 24, 52, 74 and 96 degrees of opening (closed, flat against the lid, is the
  first click). Standing on the bottom long edge it leans back at about 16, 25, 35 and 45 degrees.
- **Prop (portrait):** 14 wide, hinge near the +X end of the lid back, hanging toward -X when
  closed. One click at 92 degrees opening gives about 12.5 degrees lean back with the case on
  its +X short edge.
- The case rests on its back-bottom edge and the flap's free end (a case that leans back pivots
  on the back edge). A rubber or felt dot on the free end helps on smooth desks.

## Assembly

1. Place the panel face down in the front shell (the glass against the front plate).
2. Route the power cable into its notch in the top wall (lay it in from the back).
3. Press the lid on. The six hooks snap into the wall slots.
4. The HDMI plug goes in from outside through its notch in the top wall.
5. Kickstand: slide the two blocks' pins into the knuckle ends of the flap (spring block at the
   cam end, pins pointing at each other), then set the whole assembly on the lid back and press
   both blocks' two leg pairs into their four slots together, square to the lid, until the barbs click. The
   slots hold the blocks apart and so keep the flap captured.
6. Landscape: set the case on its bottom long edge (the flex-cable side), swing the main flap
   out to a click and lean the case back onto it. Portrait: stand it on the +X short edge and
   open the prop to its click. Never stand it on the top edge, where the cables exit. Fold the
   flaps flat for carrying.

Release: push each hook in through its wall slot with a small screwdriver and lift the lid.
