"""Adjustable desk stand: base (pivot towers + notched rack), cradle, strut. No hardware.

Stand frame: X along the case edge, +Y toward the back, Z up, base underside on Z = 0.
This frame is right-handed; it is NOT the case's model frame (see build.py).
Cradle frame (tilt 0): X as above, Y = s (front to back), Z = t (up along the case).
Tilting rotates the cradle about the pivot axis (parallel to X) so its top moves toward +Y.
Strut frame: X across the width, Y = a (pin axis toward foot axis), Z = u (thickness).
"""
import math
from build123d import Axis, Cylinder, Plane, Polygon, Pos, Rot, Text, extrude
from at070 import params as p
from at070.geom import box

_EPS = 0.5       # cutter overshoot (mm)
_TIGHT = 1.0     # overlap used to fuse touching solids


# ---------------------------------------------------------------- helpers

def _prism(pts, x0, x1):
    """Polygon given as (Y, Z) points, extruded along X from x0 to x1."""
    return extrude(Plane.YZ.offset(x0) * Polygon(*pts, align=None), amount=x1 - x0)


def _cyl_x(y, z, r, x0, x1):
    """Cylinder with its axis parallel to X through (y, z)."""
    return Pos((x0 + x1) / 2, y, z) * (Rot(Y=90) * Cylinder(r, abs(x1 - x0)))


def _flat_cut_h(r):
    """Depth of the flat of width pivot_pin_flat_w at the bottom of a round pin of radius r."""
    return r - math.sqrt(r * r - (p.pivot_pin_flat_w / 2) ** 2)


def _pin_x(y, z, r, x0, x1, flat=-1):
    """Round pin along X with a small flat on its bottom (flat=-1) or top (flat=+1) so it sits
    on the bed in the print orientation."""
    pin = _cyl_x(y, z, r, x0, x1)
    h = _flat_cut_h(r)
    z0, z1 = (z - r - 1, z - r + h) if flat < 0 else (z + r - h, z + r + 1)
    cut = box(min(x0, x1) - 1, max(x0, x1) + 1, y - r - 1, y + r + 1, z0, z1)
    return pin - cut


def c_socket(pin_d, y, z, opening, x0, x1, mouth, reach=None):
    """Cutter for a snap-in C-socket along X. Hole diameter pin_d + 2*pivot_clear, with an entry
    slot (width pin_d - 2*snap_interf) leaving the hole toward `opening` ('up' = +Z, 'back' = +Y)
    and a 45 deg lead-in chamfer at the mouth. `mouth` = distance from the hole axis to the block
    surface along the opening direction, measured at the slot edge. `reach` = how far the cutter
    extends along the opening direction (default mouth + overshoot; curved surfaces need more)."""
    hw = (pin_d - 2 * p.snap_interf) / 2
    ch = p.socket_chamfer
    top = reach if reach is not None else mouth + _EPS
    w_top = hw + (top - (mouth - ch))           # the lead-in continues at 45 deg to the top
    uv = [(-hw, 0), (hw, 0), (hw, mouth - ch), (w_top, top), (-w_top, top), (-hw, mouth - ch)]
    if opening == "up":
        pts = [(y + u, z + v) for u, v in uv]
    elif opening == "back":
        pts = [(y + v, z + u) for u, v in uv]
    else:
        raise ValueError(opening)
    hole = _cyl_x(y, z, pin_d / 2 + p.pivot_clear, x0, x1)
    return hole + _prism(pts, x0, x1)


# ---------------------------------------------------------------- cradle profile and pivot height

def _cradle_profile():
    """Cradle side profile as (s, t) points at tilt 0."""
    c, ft = p.cradle_chamfer, p.cradle_floor_t
    s_back = p.cradle_s_total
    s_rest0 = s_back - p.cradle_rest_t
    return [(0.0, -ft), (s_back - c, -ft), (s_back, -ft + c), (s_back, p.cradle_rest_h),
            (s_rest0, p.cradle_rest_h), (s_rest0, 0.0), (p.cradle_lip_wall, 0.0),
            (p.cradle_lip_wall, p.cradle_lip_h), (0.0, p.cradle_lip_h)]


def _rot_rel(s, t, theta_deg):
    """(s, t) -> (dY, dZ) from the pivot axis after tilting by theta (top moves toward +Y)."""
    a = math.radians(theta_deg)
    ds, dt = s - p.pivot_pin_s, t - p.pivot_pin_t
    return ds * math.cos(a) + dt * math.sin(a), -ds * math.sin(a) + dt * math.cos(a)


def _thetas():
    n = int(round(p.tilt_max_deg / p.tilt_step_deg))
    return [i * p.tilt_step_deg for i in range(n + 1)]


def _compute_pivot_z():
    """Smallest axis height keeping the cradle's lowest point swing_clearance above the base top
    for every tilt in [0, tilt_max] (sampled every tilt_step/10 degrees)."""
    steps = int(round(p.tilt_max_deg * 10 / p.tilt_step_deg))
    low = min(_rot_rel(s, t, p.tilt_max_deg * i / steps)[1]
              for i in range(steps + 1) for s, t in _cradle_profile())
    return p.stand_base_t + p.swing_clearance - low


PIVOT_Z = _compute_pivot_z()


def pivot_z():
    return PIVOT_Z


def lowest_cradle_z(theta):
    """Analytic lowest cradle point (profile vertices) in the stand frame at tilt theta."""
    return PIVOT_Z + min(_rot_rel(s, t, theta)[1] for s, t in _cradle_profile())


# ---------------------------------------------------------------- linkage

def _strut_pin_st():
    """Strut pin axis in the cradle frame (s, t)."""
    return p.cradle_s_total + p.strut_lug_out - p.strut_pin_to_end, p.strut_attach_t


def strut_pin_axis(theta):
    """Strut pin axis (Y, Z) in the stand frame at tilt theta."""
    dy, dz = _rot_rel(*_strut_pin_st(), theta)
    return dy, PIVOT_Z + dz


def foot_z():
    """Height of the notch (and foot) axis."""
    return p.stand_base_t + p.rack_h - p.notch_depth + p.notch_r


def foot_axis(theta):
    """Foot axis (Y, Z) at tilt theta: strut_len from the pin axis, behind it."""
    ay, az = strut_pin_axis(theta)
    zf = foot_z()
    return ay + math.sqrt(p.strut_len ** 2 - (az - zf) ** 2), zf


def notch_ys():
    return [foot_axis(th)[0] for th in _thetas()]


def notch_angles():
    return _thetas()


def base_y_range():
    return -p.base_front_margin, max(notch_ys()) + p.base_back_margin


def tower_r():
    return p.pivot_pin_d / 2 + p.pivot_clear + p.tower_wall


# ---------------------------------------------------------------- parts

def stand_cradle():
    """Cradle at tilt 0, in the cradle frame (floor underside at Z = -cradle_floor_t)."""
    hw = p.cradle_w / 2
    body = _prism(_cradle_profile(), -hw, hw)

    # pivot pins (axis s = pivot_pin_s, t = pivot_pin_t), coaxial, one per side
    x_out = hw + p.pivot_side_gap + p.pivot_block_t + p.pivot_pin_extra
    for sg in (1, -1):
        body = body + _pin_x(p.pivot_pin_s, p.pivot_pin_t, p.pivot_pin_r,
                             sg * (hw - _TIGHT), sg * x_out)

    # strut lugs with C-sockets opening backward, 45 deg gussets below
    s_rest = p.cradle_s_total
    s_axis, t_axis = _strut_pin_st()
    half_h = p.strut_pin_d / 2 + p.pivot_clear + p.strut_lug_wall
    zb, zt = t_axis - half_h, t_axis + half_h
    s_end = s_rest + p.strut_lug_out
    for sg in (1, -1):
        xa = p.strut_w / 2 + p.strut_lug_gap
        xb = xa + p.strut_lug_t
        x0, x1 = (xa, xb) if sg > 0 else (-xb, -xa)
        lug = box(x0, x1, s_rest - _TIGHT, s_end, zb, zt)
        gusset_h = s_end - s_rest
        lug = lug + _prism([(s_rest - _TIGHT, zb - gusset_h), (s_rest, zb - gusset_h),
                            (s_end, zb), (s_rest - _TIGHT, zb)], x0, x1)
        lug = lug - c_socket(p.strut_pin_d, s_axis, t_axis, "back", x0 - _EPS, x1 + _EPS,
                             p.strut_pin_to_end)
        body = body + lug
    return body.clean()


def _tower(sg):
    r = tower_r()
    xa = p.cradle_w / 2 + p.pivot_side_gap
    x0, x1 = (xa, xa + p.pivot_block_t) if sg > 0 else (-xa - p.pivot_block_t, -xa)
    z0 = p.stand_base_t / 2
    t = _prism([(-r, z0), (r, z0), (r, PIVOT_Z), (-r, PIVOT_Z)], x0, x1)
    t = t + _cyl_x(0.0, PIVOT_Z, r, x0, x1)
    hw = (p.pivot_pin_d - 2 * p.snap_interf) / 2
    sock = c_socket(p.pivot_pin_d, 0.0, PIVOT_Z, "up", x0 - _EPS, x1 + _EPS,
                    math.sqrt(r * r - hw * hw), reach=r + _EPS)
    return t - sock


def stand_base(labels=True):
    """Base plate with two pivot towers, the notched rack and (optionally) angle labels."""
    hw = (p.cradle_w + 2 * (p.pivot_side_gap + p.pivot_block_t)) / 2
    y0, y1 = base_y_range()
    plate = box(-hw, hw, y0, y1, 0, p.stand_base_t)
    plate = plate.fillet(p.stand_corner_r, plate.edges().filter_by(Axis.Z))

    ys = notch_ys()
    rack_hw = (p.strut_w + p.rack_extra_w) / 2
    ry0 = min(ys) - p.notch_r - p.rack_end_margin
    ry1 = max(ys) + p.notch_r + p.rack_end_margin
    base = plate + box(-rack_hw, rack_hw, ry0, ry1, p.stand_base_t - _TIGHT,
                       p.stand_base_t + p.rack_h)
    zf = foot_z()
    for y in ys:
        base = base - _cyl_x(y, zf, p.notch_r, -rack_hw - _EPS, rack_hw + _EPS)

    for sg in (1, -1):
        base = base + _tower(sg)

    if labels:
        for th, y in zip(_thetas(), ys):
            txt = Text(str(int(round(th))), p.label_size)       # reads along +X, up = +Y
            base = base + Pos(p.label_x, y, p.stand_base_t) * extrude(txt, amount=p.label_h)
    return base.clean()


def _strut_foot_local():
    """Foot axis in the strut frame (a, u); its distance from the pin axis is strut_len. The foot
    sticks out foot_toe below the bar's lower face (u = -strut_t/2) so the bar clears the rack
    in front of the notch."""
    du = -p.strut_t / 2 + p.foot_r - p.foot_toe
    return math.sqrt(p.strut_len ** 2 - du * du), du


def stand_strut():
    """Strut in its own frame (pin axis at the origin, bar between u = -strut_t/2 and +strut_t/2,
    foot toe below the lower face). Print it rotated 180 deg about Y (build.py) so the flat
    upper face is on the bed."""
    lf, du = _strut_foot_local()
    hw = p.strut_w / 2
    rt = p.strut_t / 2
    prof = [(0.0, -rt), (lf, -rt), (lf, rt), (0.0, rt)]
    bar = _prism(prof, -hw, hw)
    bar = bar + _cyl_x(0.0, 0.0, rt, -hw, hw)
    bar = bar + _cyl_x(lf, du, p.foot_r, -hw, hw)            # foot, full width
    half = hw + p.strut_lug_gap + p.strut_lug_t
    bar = bar + _pin_x(0.0, 0.0, p.strut_pin_d / 2, -half, half, flat=+1)
    return bar.clean()


# ---------------------------------------------------------------- poses and case

def _place(shape, theta):
    """Cradle-frame shape -> stand frame at tilt theta."""
    return (Pos(0, 0, PIVOT_Z) * Rot(X=-theta)
            * Pos(0, -p.pivot_pin_s, -p.pivot_pin_t) * shape)


def cradle_pose(theta):
    return _place(stand_cradle(), theta)


def case_box(landscape):
    """Case as a box in the cradle frame (tilt 0): on the groove floor, against the back rest.
    Landscape: long edge down, height along t = outer_h. Portrait: short edge down, outer_w."""
    w, h = (p.outer_w, p.outer_h) if landscape else (p.outer_h, p.outer_w)
    s1 = p.cradle_s_total - p.cradle_rest_t
    return box(-w / 2, w / 2, s1 - p.case_depth, s1, 0.0, h)


def case_pose(theta, landscape):
    return _place(case_box(landscape), theta)


def case_com(theta, landscape):
    """Case center of mass (Y, Z) in the stand frame."""
    h = p.outer_h if landscape else p.outer_w
    s = p.cradle_s_total - p.cradle_rest_t - p.case_depth / 2
    dy, dz = _rot_rel(s, h / 2, theta)
    return dy, PIVOT_Z + dz


def _strut_at(pin, foot):
    """Strut placed with its pin axis at `pin` and its foot axis at `foot` (stand-frame Y, Z)."""
    lf, du = _strut_foot_local()
    beta = math.atan2(du, lf)
    gamma = math.atan2(foot[1] - pin[1], foot[0] - pin[0])
    return Pos(0, pin[0], pin[1]) * Rot(X=math.degrees(gamma - beta)) * stand_strut()


def strut_pose(theta):
    return _strut_at(strut_pin_axis(theta), foot_axis(theta))


def strut_folded_pose():
    """Strut folded down against the back of the rest (cradle upright, tilt 0)."""
    pin = strut_pin_axis(0.0)
    return _strut_at(pin, (pin[0], pin[1] - p.strut_len))
