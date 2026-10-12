"""Built-in kickstand: main flap (landscape), prop (portrait) and snap-in hinge blocks.

Canonical frame (used for every kickstand part before it is placed on the lid): hinge axis along
X through (Y 0, Z ks_axis_z), lid back plane at Z = 0 (the lid is at negative Z), the flap hangs
toward -Y when closed, the detent spring is on the +Y side of the axis, the snap legs on the -Y
side. `main_parts` / `prop_parts` place canonical parts on the lid in the case's model frame
(see README); build.py mirrors them to the real parts like the lid.
"""
import math
from build123d import Axis, Pos, Rot
from at070 import params as p
from at070.geom import box, c_socket, cyl_x, prism_x

EPS = 0.5          # cutter overshoot (mm)
FUSE = 0.1         # overlap used to fuse touching solids


# ---------------------------------------------------------------- derived block geometry

def leg_y():
    """Y positions (canonical) of the two snap legs: (yA0, yA1, yB0, yB1). Leg A is the outer
    one (barb toward -Y), leg B the inner one (barb toward +Y)."""
    yb1 = -p.ks_block_r - p.ks_leg_chan
    yb0 = yb1 - p.ks_leg_t
    ya1 = yb0 - p.ks_leg_slit
    ya0 = ya1 - p.ks_leg_t
    return ya0, ya1, yb0, yb1


def leg_z():
    """Z positions (canonical, lid back = 0) of the leg: (z_tip, z_catch, z_slit_top)."""
    z_catch = -(p.lid_plate_t + p.ks_leg_play)
    out = p.ks_slot_clear + p.ks_barb_catch
    return z_catch - p.ks_barb_flat - out, z_catch, z_catch + p.ks_leg_len


def leg_strain():
    """Snap-leg strain at assembly: 1.5 * t * y / L^2, y = barb overlap past the slot edge."""
    return 1.5 * p.ks_leg_t * p.ks_barb_catch / p.ks_leg_len ** 2


def leaf_strain():
    """Detent leaf strain: same cantilever formula as lid.clip_strain(); the tip is deflected
    by the preload plus the notch depth when it rides the cam between notches."""
    return 1.5 * p.ks_leaf_t * (p.ks_preload + p.ks_notch_depth) / p.ks_leaf_len ** 2


def _beta():
    """Half-angle of the V notch measured from the radial direction."""
    return math.radians(90.0 - p.ks_flank_deg)


def notch_apex_depth():
    """Depth of the virtual (unrounded) V apex below the cam surface, chosen so the tip drops
    exactly ks_notch_depth when seated against both flanks."""
    return p.ks_notch_depth + p.ks_tip_r * (1.0 / math.sin(_beta()) - 1.0)


def tip_seated_dist():
    """Tip center distance from the axis when seated in a notch."""
    return p.ks_knuckle_r + p.ks_tip_r / math.sin(_beta()) - notch_apex_depth()


def tip_rest_y():
    """Tip center distance from the axis with the leaf relaxed (seated minus the preload)."""
    return tip_seated_dist() - p.ks_preload


def notch_width():
    """Width of a notch at the cam surface (flat approximation)."""
    return 2 * notch_apex_depth() * math.tan(_beta())


def min_notch_pitch_deg():
    return math.degrees((notch_width() + p.ks_notch_wall) / p.ks_knuckle_r)


def leaf_stiffness():
    """Leaf spring rate at the tip, N/mm (cantilever, end load, full leaf height)."""
    w = p.ks_axis_z + p.ks_leaf_top
    return p.ks_leaf_E * w * p.ks_leaf_t ** 3 / (4 * p.ks_leaf_len ** 3)


def holding_torque():
    """Estimated detent torque about the hinge axis needed to climb out of a notch, N*mm:
    leaf force at the flank top, times tan(flank angle) for the tangential share, times the cam
    radius. Frictionless; friction raises it, edge rounding lowers it."""
    f = leaf_stiffness() * (p.ks_preload + p.ks_notch_depth)
    return f * math.tan(math.radians(p.ks_flank_deg)) * p.ks_knuckle_r


def _notch_cutter(theta_deg, x0, x1):
    """Rounded V notch cutter (canonical Y/Z section, along X) at body angle theta."""
    be = _beta()
    ra = p.ks_notch_apex_r
    za = p.ks_axis_z
    apex = p.ks_knuckle_r - notch_apex_depth()          # radial position of the virtual apex
    far = notch_apex_depth() + 2.0                      # flanks run this far past the apex
    t = math.radians(theta_deg)
    er, eu = (math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))

    def pt(s, u):
        return (s * er[0] + u * eu[0], za + s * er[1] + u * eu[1])
    # tangent points of the apex circle on the flanks: distance ra/tan(be) along the flank
    d = ra / math.tan(be)
    tp = [(apex + d * math.cos(be), sg * d * math.sin(be)) for sg in (1, -1)]
    out = [(apex + far * math.cos(be), sg * far * math.sin(be)) for sg in (1, -1)]
    poly = prism_x([pt(*tp[0]), pt(*out[0]), pt(*out[1]), pt(*tp[1])], x0, x1)
    cs = apex + ra / math.sin(be)
    cy, cz = pt(cs, 0.0)
    return poly + cyl_x(cy, cz, ra, x0, x1)


# ---------------------------------------------------------------- parts (canonical frame)

def hinge_block(x0=0.0, spring=False, tip=True):
    """Hinge block from x0 to x0 + ks_block_w. Pad on the lid back (Z 0), C-socket for a pin stub
    (axis Y 0, Z ks_axis_z, opening +Z, through the block), two snap legs on the -Y side that
    pass through a lid slot, barbs catching the lid underside. With spring=True a detent leaf
    spring runs from the block face x0 toward -X over the flap's cam (+Y side)."""
    x1 = x0 + p.ks_block_w
    sw, za = p.ks_block_r, p.ks_axis_z
    body = box(x0, x1, -sw, sw, 0, za) + cyl_x(0, za, sw, x0, x1)
    ya0, ya1, yb0, yb1 = leg_y()
    z_tip, z_catch, z_slit = leg_z()
    out = p.ks_slot_clear + p.ks_barb_catch
    zf = z_catch - p.ks_barb_flat
    body += box(x0, x1, ya0, -sw + 0.3, z_slit, z_slit + p.ks_cap_t)            # cap
    body += box(x0, x1, ya0, ya1, z_tip, z_slit + FUSE)                          # leg A
    body += box(x0, x1, yb0, yb1, z_tip, z_slit + FUSE)                          # leg B
    body += prism_x([(ya0 + FUSE, z_catch), (ya0 - out, z_catch), (ya0 - out, zf),
                     (ya0, z_tip), (ya0 + FUSE, z_tip)], x0, x1)
    body += prism_x([(yb1 - FUSE, z_catch), (yb1 + out, z_catch), (yb1 + out, zf),
                     (yb1, z_tip), (yb1 - FUSE, z_tip)], x0, x1)
    hw = (p.ks_pin_d - 2 * p.ks_snap_interf) / 2
    sock = c_socket(p.ks_pin_d, 0.0, za, x0 - EPS, x1 + EPS, math.sqrt(sw * sw - hw * hw),
                    sw + EPS, p.ks_pin_clear, p.ks_snap_interf, p.ks_socket_chamfer)
    body -= sock
    if spring:
        y_in = p.ks_knuckle_r + p.ks_leaf_clear
        y_out = y_in + p.ks_leaf_t
        z_top = za + p.ks_leaf_top
        body += box(x0, x1, sw - 0.3, y_out, 0, z_top)                           # root web
        xt = x0 - p.ks_leaf_len
        body += box(xt, x0 + FUSE, y_in, y_out, 0, z_top)                        # leaf
        if tip:
            ty = tip_rest_y()
            body += cyl_x(ty, za, p.ks_tip_r, xt, xt + p.ks_tip_len)
            body += box(xt, xt + p.ks_tip_len, ty, y_in + FUSE, za - p.ks_tip_r, za + p.ks_tip_r)
    return body.clean()


def _plate(hw, length):
    """Flap plate with rounded free-end corners (the free-end edge stays sharp: it is the foot)."""
    z0, z1 = p.ks_gap, p.ks_gap + p.ks_plate_t
    plate = box(-hw, hw, -length, 0, z0, z1)
    corners = plate.edges().filter_by(Axis.Z).filter_by_position(Axis.Y, -length - 1e-3, -length + 1e-3)
    return plate.fillet(min(p.ks_flap_corner_r, hw / 2), corners)


def flap(width, length, notches, pin_left=True):
    """Flap: plate (X +-width/2, Y -length..0, underside at Z ks_gap) with a knuckle along the
    hinge edge (tangent to the plate underside), a notched cam of ks_cam_len beyond the +X plate
    end, and pin stubs at both ends (only the +X one if pin_left is False). `notches` = flap
    opening angles (degrees); the notch for opening a sits at body angle a, measured from +Y
    toward +Z, so the spring (+Y side) falls into it when the flap is open by a."""
    hw = width / 2
    rk, za = p.ks_knuckle_r, p.ks_axis_z
    kn = cyl_x(0, za, rk, -hw, hw + p.ks_cam_len)
    for a in notches:
        kn -= _notch_cutter(a, hw, hw + p.ks_cam_len + EPS)
    out = kn + _plate(hw, length)
    pr = p.ks_pin_d / 2
    out += cyl_x(0, za, pr, hw + p.ks_cam_len - EPS, hw + p.ks_cam_len + p.ks_pin_len)
    if pin_left:
        out += cyl_x(0, za, pr, -hw - p.ks_pin_len, -hw + EPS)
    return out.clean()


def slot_box(x0):
    """Lid slot (canonical) for a block starting at x0."""
    c = p.ks_slot_clear
    ya0, _, _, yb1 = leg_y()
    return box(x0 - c, x0 + p.ks_block_w + c, ya0 - c, yb1 + c, -(p.lid_plate_t + EPS), EPS)


def pose_flap(shape, opening):
    """Flap opened by `opening` degrees about its hinge axis (free end toward +Z)."""
    return Pos(0, 0, p.ks_axis_z) * Rot(X=-opening) * Pos(0, 0, -p.ks_axis_z) * shape


# ---------------------------------------------------------------- placement on the lid

def block_x0s(width):
    """Canonical x0 of the plain block (at -X) and the spring block (at +X)."""
    hw = width / 2
    return -hw - p.ks_ax_gap - p.ks_block_w, hw + p.ks_cam_len + p.ks_ax_gap


def main_placement():
    return Pos(p.aa_cx, p.ks_main_y, p.z_lid_top)


def prop_placement():
    # Rot(Z=-90): canonical +X -> model -Y, canonical -Y (flap side) -> model -X,
    # canonical +Y (spring side) -> model +X.
    return Pos(p.ks_prop_x, p.ks_prop_yc, p.z_lid_top) * Rot(Z=-90)


def _assembly(place, width, length, notches, opening, tip):
    xp, xs = block_x0s(width)
    return {"flap": place * pose_flap(flap(width, length, notches), opening),
            "block_plain": place * hinge_block(xp),
            "block_spring": place * hinge_block(xs, spring=True, tip=tip)}


def main_parts(opening=0.0, tip=True):
    return _assembly(main_placement(), p.ks_main_w, p.ks_main_len, p.ks_main_notches, opening, tip)


def prop_parts(opening=0.0, tip=True):
    return _assembly(prop_placement(), p.ks_prop_w, p.ks_prop_len, p.ks_prop_notches, opening, tip)


def slot_cutters():
    """Lid slot cutters (model frame), one per hinge block."""
    res = []
    for place, width in ((main_placement(), p.ks_main_w), (prop_placement(), p.ks_prop_w)):
        for x0 in block_x0s(width):
            res.append(place * slot_box(x0))
    return res


def all_parts(main_opening=0.0, prop_opening=0.0, tip=True):
    """Every kickstand solid in the model frame, keyed by name."""
    res = {}
    for pre, parts in (("main", main_parts(main_opening, tip)), ("prop", prop_parts(prop_opening, tip))):
        for k, v in parts.items():
            res[f"{pre}_{k}"] = v
    return res


# ---------------------------------------------------------------- stability (2D, side view)

def _foot_points(axis_u, length, opening):
    """Free-end corners (u, z) of a flap opened by `opening` deg; u is Y (landscape) or X
    (portrait), the flap hanging toward -u when closed."""
    zh = p.z_lid_top + p.ks_axis_z
    a = math.radians(opening)
    d = (-math.cos(a), math.sin(a))          # along the plate, hinge to free end
    n = (-math.sin(a), -math.cos(a))         # toward the lid side of the plate
    return [(axis_u + length * d[0] + s * n[0], zh + length * d[1] + s * n[1])
            for s in (p.ks_knuckle_r, p.ks_knuckle_r - p.ks_plate_t)]


def support(orientation, opening):
    """Case resting on its back-bottom edge (including the lid edge fillet) and on the flap's
    free end. orientation 'landscape' (main flap, on the Y = outer_y0 edge) or 'portrait'
    (prop, on the X = outer_x1 edge). Returns a dict: tilt (deg from vertical, leaning back),
    contact (u, z of the fillet center), foot (u, z), margin_contact / margin_foot (horizontal
    distance of the COM from each, positive = COM between them)."""
    e = p.edge_fillet
    zc = (-p.front_thickness + p.z_lid_top) / 2
    if orientation == "landscape":
        sg, bu, com_u = 1.0, p.outer_y0 + e, (p.outer_y0 + p.outer_y1) / 2
        feet = _foot_points(p.ks_main_y, p.ks_main_len, opening)
    else:
        sg, bu, com_u = -1.0, p.outer_x1 - e, (p.outer_x0 + p.outer_x1) / 2
        feet = _foot_points(p.ks_prop_x, p.ks_prop_len, opening)
    bz = p.z_lid_top - e

    def up(l):
        r = math.radians(l)
        return sg * math.cos(r), -math.sin(r)

    def f(l):
        u = up(l)
        return min(u[0] * a + u[1] * b for a, b in feet) - (u[0] * bu + u[1] * bz - e)

    lo, prev = None, f(0.0)
    for i in range(1, 1781):
        v = f(i * 0.05)
        if prev > 0 >= v:
            lo = (i - 1) * 0.05, i * 0.05
            break
        prev = v
    if lo is None:
        return None
    a, b = lo
    for _ in range(40):
        m = (a + b) / 2
        a, b = (m, b) if f(m) > 0 else (a, m)
    tilt = (a + b) / 2
    r = math.radians(tilt)
    h = (sg * math.sin(r), math.cos(r))
    u = up(tilt)
    foot = min(feet, key=lambda q: u[0] * q[0] + u[1] * q[1])
    axis = (p.ks_main_y if orientation == "landscape" else p.ks_prop_x, p.z_lid_top + p.ks_axis_z)
    return {"tilt": tilt, "contact": (bu, bz), "foot": foot, "axis": axis, "h": h,
            "margin_contact": h[0] * (com_u - bu) + h[1] * (zc - bz),
            "margin_foot": h[0] * (foot[0] - com_u) + h[1] * (foot[1] - zc),
            "opening": opening}


def main_table():
    """Support state for each open main-flap notch."""
    return [support("landscape", a) for a in p.ks_main_notches if a > 0]


def prop_state():
    return support("portrait", max(p.ks_prop_notches))


def load_torque(state, weight=None):
    """Torque about the hinge axis (N*mm) that the case weight puts on the flap through its
    foot. The weight acts at the COM; the vertical reactions at the back contact edge and at the
    foot split it by the COM position (frictionless); the foot reaction acts at the horizontal
    distance of the foot from the hinge axis. It tries to fold the flap toward the lid."""
    w = p.ks_case_weight if weight is None else weight
    mc, mf = state["margin_contact"], state["margin_foot"]
    r_foot = w * mc / (mc + mf)
    h, fu, fz = state["h"], state["foot"][0], state["foot"][1]
    au, az = state["axis"]
    arm = abs(h[0] * (fu - au) + h[1] * (fz - az))
    return r_foot * arm


def detent_table():
    """Rows (name, opening, tilt, foot_reaction_N, arm_mm, load_Nmm, hold_Nmm, ratio) for every
    open notch of the main flap and the prop."""
    rows = []
    hold = holding_torque()
    for name, states in (("main", main_table()), ("prop", [prop_state()])):
        for st in states:
            load = load_torque(st)
            mc, mf = st["margin_contact"], st["margin_foot"]
            rows.append({"flap": name, "opening": st["opening"], "tilt": st["tilt"],
                         "foot_reaction": p.ks_case_weight * mc / (mc + mf),
                         "load": load, "hold": hold, "ratio": hold / load})
    return rows
