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
hdmi_x = -10.45           # HDMI socket center X
hdmi_mouth_y = 37.6       # HDMI socket mouth Y
hdmi_z = 12.0             # HDMI socket center height
plug_w = 21.0             # HDMI plug body width (X)
plug_t = 11.0             # HDMI plug body thickness (Z)
plug_len = 45.0           # HDMI plug body length (Y)
plug_cable_d = 6.0        # cable diameter behind plug
plug_cable_len = 30.0     # cable length modeled behind plug
power_x = -57.0           # power cable X
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

hdmi_notch_margin = 1.0   # notch margin per side around plug
hdmi_notch_w = plug_w + 2 * hdmi_notch_margin   # 23
hdmi_notch_z0 = hdmi_z - plug_t / 2 - 1.0       # 5.5
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
tilt_deg = 15.0           # tilt back from vertical
stand_w = 100.0           # stand width (along case edge)
stand_d = 110.0           # stand depth
stand_base_t = 4.0        # base thickness
stand_corner_r = 6.0      # base corner radius
groove_clearance = 1.0    # groove width minus case depth
case_depth = front_thickness + z_lid_top        # 23.4
groove_w = case_depth + groove_clearance        # 24.4
lip_h = 10.0              # front lip height along tilt
lip_wall = 4.0            # front lip thickness
rest_t = 4.0              # back rest thickness
rest_top_z = 70.0         # back rest height above base underside
com_min_edge = 25.0       # min COM distance from base front/back edges

# ---- Coupons ----
coupon_fit_z = 6.5        # fit-frame cut height
coupon_box = (-72.0, 5.0, 30.0, 65.0)   # x0, x1, y0, y1 of top-edge coupon

# ---- Printer ----
bed_limit = 250.0
