"""All dimensions in mm. Coordinates: origin = panel center on the glass face; see README."""
import math

# ---- Panel (datasheet) ----
panel_w = 164.90          # panel outline width (X)
panel_h = 100.00          # panel outline height (Y)
panel_t = 5.70            # panel thickness (Z)
aa_w = 154.08             # active area width
aa_h = 85.92              # active area height
aa_margin_left = 3.92     # outline edge to AA, left (seen from front)
aa_margin_bottom = 9.30   # outline edge to AA, bottom
aa_x0 = -panel_w / 2 + aa_margin_left          # AA left edge X
aa_y0 = -panel_h / 2 + aa_margin_bottom        # AA bottom edge Y
aa_cx = aa_x0 + aa_w / 2                       # AA center X (-1.49)
aa_cy = aa_y0 + aa_h / 2                       # AA center Y (+2.26)
fpc_center_x = -1.50      # FPC center X
fpc_width = 37.0          # FPC width at the panel
fpc_bulge = 2.5           # FPC bulge below the panel bottom edge

# ---- Photo estimates (uncertain +-3) ----
board_x0 = -48.55         # driver board min X
board_x1 = 22.95          # driver board max X
board_y0 = -18.0          # driver board min Y
board_y1 = 34.0           # driver board max Y
board_adhesive = 1.5      # adhesive pad thickness
board_pcb = 1.6           # PCB thickness
board_comp = 5.0          # tallest component above PCB
board_keepout_margin = 2.0  # keep-out growth in X/Y
board_top_z = panel_t + board_adhesive + board_pcb + board_comp  # 13.8
hdmi_x = -8.5             # HDMI socket center X (ruler photos 2026-10-11, +-1)
hdmi_mouth_y = 36.2       # HDMI socket mouth Y (ruler photos 2026-10-11)
hdmi_z = 13.7             # HDMI socket/plug center height (ruler 2026-10-11: 8.0 above panel back)
plug_w = 21.0             # HDMI plug body width (X)
plug_t = 8.9              # HDMI plug body thickness (Z) (measured 7/20 in)
plug_len = 45.0           # HDMI plug body length (Y)
plug_cable_d = 6.0        # cable diameter behind plug
plug_cable_len = 30.0     # cable length modeled behind plug
power_x = -57.0           # power cable X (cable is flexible; any nearby X works)
power_z = 10.0            # power cable center Z
power_cable_d = 4.0       # USB cable diameter
power_shrink_d = 6.0      # heat-shrink diameter
power_shrink_y0 = 30.0    # heat-shrink start Y
power_shrink_y1 = 44.0    # heat-shrink end Y (inside the case)
power_cable_y0 = 25.0     # cable start Y
power_cable_y1 = 85.0     # cable end Y

# ---- Shell ----
front_thickness = 2.0     # front plate thickness (Z -2..0)
window_margin = 0.6       # window margin around AA per side
window_chamfer = 1.0      # 45 deg chamfer on window front edge
panel_clearance = 0.4     # pocket clearance (left/right/top/bottom)
fpc_relief = 3.0          # extra pocket below panel bottom
wall = 2.4                # wall thickness
z_rim = 19.0              # shell rim Z
corner_r = 4.0            # outer vertical corner radius
edge_fillet = 1.5         # front/back perimeter fillet
# Pocket: smallest rectangle centered on the AA center containing panel+clearance (+FPC relief below)
_need_x0 = -panel_w / 2 - panel_clearance
_need_x1 = panel_w / 2 + panel_clearance
_need_y0 = -panel_h / 2 - panel_clearance - fpc_relief
_need_y1 = panel_h / 2 + panel_clearance
pocket_half_w = max(aa_cx - _need_x0, _need_x1 - aa_cx)
pocket_half_h = max(aa_cy - _need_y0, _need_y1 - aa_cy)
pocket_x0 = aa_cx - pocket_half_w
pocket_x1 = aa_cx + pocket_half_w
pocket_y0 = aa_cy - pocket_half_h
pocket_y1 = aa_cy + pocket_half_h
outer_x0 = pocket_x0 - wall
outer_x1 = pocket_x1 + wall
outer_y0 = pocket_y0 - wall
outer_y1 = pocket_y1 + wall
outer_w = outer_x1 - outer_x0   # case long side
outer_h = outer_y1 - outer_y0   # case short side

# panel-edge-with-clearance positions (where locating blocks stop)
lb_left_x = -panel_w / 2 - panel_clearance
lb_top_y = panel_h / 2 + panel_clearance
lb_bottom_y = -panel_h / 2 - panel_clearance
lb_w = 10.0               # locating block length along its wall
lb_h = panel_t            # locating block height (Z 0..panel_t)
lb_bottom_xs = (-60.0, 60.0)   # bottom wall block centers X
lb_left_ys = (-30.0, 30.0)     # left wall block centers Y
lb_top_xs = (30.0, 70.0)       # top wall block centers X

# HDMI alcove: the top wall and lid step in to the socket over the plug width, so the socket
# is visible and the plug goes straight in. The alcove's walls and floor hang from the lid
# (the panel drops in from the back, so the shell can't reach over it).
alcove_clear = 2.0        # alcove inner side clearance per side around the plug body
alcove_wall = 1.6         # alcove side/back wall and floor thickness
alcove_floor_gap = 0.3    # alcove floor underside above the panel back
alcove_side_gap = 0.2     # shell wall cut to alcove side wall, per side
plug_slot_clear = 0.5     # back-wall slot clearance around the plug body
alcove_hw_in = plug_w / 2 + alcove_clear                 # 12.5
alcove_hw_out = alcove_hw_in + alcove_wall               # 14.1
alcove_y0 = hdmi_mouth_y + 0.4                           # back wall inner side (clear of socket)
alcove_z0 = panel_t + alcove_floor_gap                   # floor underside (6.0)
hdmi_notch_w = 2 * (alcove_hw_out + alcove_side_gap)     # shell wall cut width (28.6)
hdmi_notch_z0 = panel_t                                  # shell wall cut bottom
power_notch_w = 5.0       # power notch width
power_notch_z0 = power_z - power_notch_w / 2    # 7.5 (bottom of round end)

# ---- Lid ----
lid_plate_t = 2.4         # lid plate thickness
z_lid_top = z_rim + lid_plate_t  # 21.4
lip_z0 = 17.0             # lip bottom Z
lip_t = 1.2               # lip thickness
lip_inset = 0.3           # lip inset from inner wall face
lip_notch_extra = 2.0     # lip removed over notch width + this (total)
lip_clip_extra = 2.0      # lip removed over clip width + this (total)
lip_rib_extra = 0.6       # lip cut around ribs, per side
clip_length = 13.0        # clip length (root Z 19 to tip)
clip_thickness = 1.2      # clip thickness (3 lines at 0.4 nozzle)
clip_width = 8.0          # clip width
clip_gap = 0.2            # gap clip to wall inner face
hook_overlap = 1.3        # hook protrusion (bite into wall = overlap - gap = 1.1)
hook_height = 2.1         # hook height (Z): lead-in + 0.8 flat catch
hook_lead = 1.3           # 45 deg lead-in height (= overlap for 45 deg)
slot_clearance = 0.3      # clip slot clearance per side
slot_top_clearance = 0.1  # slot top edge above the catch face (lid play when clipped)
clip_top_xs = (-38.0, 40.0)    # top wall clip X
clip_bottom_xs = (-50.0, 50.0)  # bottom wall clip X
clip_side_y = aa_cy       # side wall clip Y
press_gap = 0.2           # rib tip gap to panel back
rib_leg = 12.0            # rib leg length
rib_t = 1.6               # rib thickness
rib_inset = 1.0           # rib inset from panel outline corners
clip_strain_max = 0.015   # allowed cantilever strain (PLA, repeated opening)

# ---- Stand ----
# Three printed parts: base (with pivot towers and a notched rack), cradle (holds the case,
# tilts about two pins), strut (props the cradle; its foot clicks into a rack notch).
# Stand frame: X along the case edge, +Y toward the back, Z up, base underside on Z = 0.
# Cradle frame: s = front to back, t = up along the case (equal to Y and Z at tilt 0).
stand_base_t = 4.0        # base plate thickness
stand_corner_r = 6.0      # base plate corner radius
groove_clearance = 1.0    # groove width minus case depth
case_depth = front_thickness + z_lid_top        # 23.4
groove_w = case_depth + groove_clearance        # 24.4
com_min_edge = 25.0       # min COM distance from base front/back edges
tilt_step_deg = 5.0       # click-in step
tilt_max_deg = 45.0       # max tilt back from vertical
pivot_clear = 0.25        # radial clearance, pin in socket hole
snap_interf = 0.35        # snap interference per side (slot narrower than the pin)
socket_chamfer = 1.0      # 45 deg lead-in at the slot mouth
# cradle
cradle_w = 88.0           # cradle width (X); must be < outer_h
cradle_floor_t = 9.0      # floor thickness (t -9..0); pivot axis sits 6 below the case bottom
cradle_lip_wall = 4.0     # front lip thickness
cradle_lip_h = 10.0       # front lip height above the groove floor
cradle_rest_t = 4.0       # back rest thickness
cradle_rest_h = 80.0      # back rest height above the groove floor
cradle_chamfer = 8.0      # 45 deg chamfer on the floor's back-bottom edge (lowers pivot_z)
cradle_s_total = cradle_lip_wall + groove_w + cradle_rest_t   # 32.4
pivot_pin_d = 6.0         # cradle pivot pin diameter
pivot_pin_r = pivot_pin_d / 2
pivot_pin_s = 3.0         # pivot axis position s
pivot_pin_t = -cradle_floor_t + pivot_pin_r    # pivot axis position t (-6): pins tangent to floor
pivot_side_gap = 0.5      # cradle side face to tower
pivot_block_t = 6.0       # tower thickness (X)
pivot_pin_extra = 0.5     # pin protrusion beyond the tower outer face
pivot_pin_flat_w = 0.6    # width of the flat at the pin bottom
strut_attach_t = 70.0     # strut pin axis t on the rest
strut_lug_gap = 0.5       # strut side to lug
strut_lug_t = 5.0         # lug thickness (X)
strut_lug_out = 9.0       # lug length behind the rest
strut_pin_to_end = 4.0    # strut pin axis to the lug's back end
strut_lug_wall = 2.0      # lug material around the socket hole
# base
base_front_margin = 25.0  # base front edge to pivot axis (Y)
base_back_margin = 12.0   # last notch to base back edge
swing_clearance = 2.0     # min gap, cradle lowest point to base top over the whole swing
tower_wall = 2.0          # tower material around the socket hole
tower_case_gap = 0.8      # min radial gap, case to tower
rack_h = 4.0              # rack height above base top
rack_extra_w = 4.0        # rack width beyond strut width
rack_end_margin = 4.0     # rack extends this far beyond first/last notch (plus notch_r)
notch_depth = 2.5         # notch depth below rack top
notch_extra_r = 0.3       # notch radius minus foot radius
notch_min_gap = 1.2       # min wall between neighboring notches
label_size = 4.5          # angle label text height
label_h = 0.6             # label emboss height
label_x = 33.0            # label center X (beside the rack)
# strut
strut_w = 40.0            # strut width (X)
strut_t = 5.0             # strut thickness
strut_len = 95.0          # pin axis to foot axis
strut_pin_d = 5.0         # strut top pin diameter
foot_r = 2.0              # strut foot radius
foot_toe = 1.3            # foot sticks out below the bar's lower face (bar clears the rack)
notch_r = foot_r + notch_extra_r

# ---- Coupons ----
coupon_fit_z = 6.5        # fit-frame cut height
coupon_box = (-72.0, 10.0, 30.0, 65.0)   # x0, x1, y0, y1 of top-edge coupon

# ---- Printer ----
bed_limit = 250.0
