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
board_adhesive = 2.0      # adhesive pad thickness (side photo 2026-10-11)
board_pcb = 1.6           # PCB thickness
board_comp = 9.2          # tallest part above PCB: flex loop 12.8 / inductor 12.3 above panel back (photo)
board_keepout_margin = 2.0  # keep-out growth in X/Y
board_top_z = panel_t + board_adhesive + board_pcb + board_comp  # 18.5 (lid underside 19.0)
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
corner_r = 7.0            # outer vertical corner radius (pocket corners follow, see pocket_r)
edge_fillet = 2.0         # lid back perimeter fillet (max ~2.2 for the 2.4 plate)
front_fillet = 3.0        # front (screen face) perimeter fillet
pocket_r = corner_r - wall  # pocket vertical corner radius (constant wall around the corners)
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

# ---- Kickstand ----
# Built into the lid back: a main flap (landscape, several click positions) and a small prop
# (portrait, one click position). Each flap has a knuckle with a pin stub at both ends that
# snaps into a hinge block; the blocks snap into slots through the lid plate. All dimensions
# are in a canonical frame: hinge axis along X through (Y 0, Z ks_axis_z above the lid back),
# the flap hangs toward -Y when closed, the lid back is the plane Z = 0, +Y is the side the
# detent spring is on, and the snap legs are on the -Y side of the socket.
ks_gap = 0.3              # closed flap underside (and knuckle bottom) above the lid back
ks_plate_t = 3.0          # flap plate thickness
ks_flap_corner_r = 5.0    # flap free-end corner radius (capped at width/4)
ks_knuckle_r = 4.0        # knuckle (and cam) radius, tangent to the plate underside
ks_axis_z = ks_gap + ks_knuckle_r   # hinge axis height above the lid back (4.3)
ks_pin_d = 5.0            # pin stub diameter
ks_pin_clear = 0.25       # radial clearance, pin in socket hole
ks_snap_interf = 0.35     # snap interference per side (slot narrower than the pin)
ks_socket_chamfer = 1.0   # 45 deg lead-in at the slot mouth
ks_socket_wall = 1.4      # block material around the socket hole
ks_ax_gap = 0.5           # axial gap, knuckle end to block
ks_block_w = 5.0          # block width along the hinge axis (also leg width)
ks_pin_len = ks_ax_gap + ks_block_w - 0.5   # pin stub length (ends 0.5 short of the block face)
ks_cam_len = 11.0         # notched cam length at one end of the knuckle
ks_block_r = ks_pin_d / 2 + ks_pin_clear + ks_socket_wall   # block half width / top radius
# hinge block snap legs (flex once, at assembly)
ks_leg_t = 1.2            # leg thickness
ks_leg_slit = 2.0         # gap between the two legs
ks_leg_chan = 0.6         # gap between the inner leg and the block body
ks_leg_len = 7.4          # leg length from the slit top to the barb catch face
ks_slot_clear = 0.2       # lid slot clearance per side
ks_barb_catch = 0.8       # barb overlap under the lid
ks_barb_flat = 0.3        # barb flat height below the catch face
ks_leg_play = 0.05        # block lift play: catch face this far below the lid underside
ks_cap_t = 1.2            # cap thickness above the slit
ks_leg_strain_max = 0.03  # allowed snap-leg strain (one-time assembly)
# detent: V notches with steep flanks on the cam, a tip riding in them on a stiff leaf spring
ks_notch_depth = 0.4      # tip drop from riding on the cam surface to seated in a notch
ks_flank_deg = 60.0       # notch flank angle from the cam surface tangent (steeper = holds more)
ks_notch_apex_r = 0.25    # rounding radius at the bottom of the V
ks_notch_wall = 0.5       # min wall between neighboring notches at the cam surface
ks_tip_r = 0.45           # spring tip radius
ks_tip_len = 3.0          # spring tip length along the axis
ks_preload = 0.0          # extra leaf deflection when the tip is seated in a notch
ks_leaf_t = 2.4           # leaf spring thickness
ks_leaf_len = 10.0        # leaf spring length (root at the block face)
ks_leaf_clear = 0.3       # leaf inner face to the cam surface
ks_leaf_top = 3.7         # leaf top above the hinge axis (leaf height ks_axis_z + this)
ks_leaf_strain_max = 0.015   # allowed leaf strain (flexes on every click)
ks_leaf_E = 2500.0        # PLA modulus used for the holding-torque estimate, N/mm^2 (estimate)
ks_case_weight = 3.5      # N, assumed case weight acting at the outline center
# main flap (landscape)
ks_main_w = 120.0         # plate width, centered on the case outline X center
ks_main_h = 60.0          # hinge axis height above the bottom edge (outer_y0)
ks_main_len = 56.0        # hinge axis to free end
ks_main_notches = (0.0, 24.0, 52.0, 74.0, 96.0)   # flap opening angles, degrees
ks_main_y = outer_y0 + ks_main_h
# prop (portrait)
ks_prop_w = 18.0          # plate width along Y
ks_prop_x = 75.0          # hinge axis X; the plate hangs toward -X when closed
ks_prop_len = 45.0        # hinge axis to free end
ks_prop_notches = (0.0, 90.0)
ks_prop_y_max = 55.4      # outer face of the +Y hinge block (clear of the lid lip)
ks_prop_yc = ks_prop_y_max - (ks_prop_w / 2 + ks_ax_gap + ks_block_w)   # plate center Y
# stability
ks_com_margin = 5.0       # min COM distance from the back contact edge and from the foot
ks_tilt_min = 16.0        # landscape: tilts must reach this low ...
ks_tilt_max = 43.0        # ... and this high
ks_lean_min = 12.0        # portrait lean range
ks_lean_max = 13.5
ks_assembly_tilt = 30.0   # kickstand_assembly.step uses the main-flap notch nearest this tilt
ks_sweep_step = 5.0       # sampling step for the rotation clearance check, degrees

# ---- Coupons ----
coupon_fit_z = 6.5        # fit-frame cut height
coupon_box = (-72.0, 10.0, 30.0, 65.0)   # x0, x1, y0, y1 of top-edge coupon

# ---- Printer ----
bed_limit = 250.0

# ---- Hinge coupon (canonical frame of the kickstand) ----
coupon_hinge_w = 19.0     # coupon flap plate width (plus the cam, the knuckle is 30 long)
coupon_hinge_len = 20.0   # coupon flap plate length
coupon_hinge_x = (-12.0, 28.0)   # lid piece X range
coupon_hinge_y = (-22.0, 18.0)   # lid piece Y range
