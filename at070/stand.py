"""Desk stand: base plate with a tilted groove the case sits in (either edge down).

Stand frame: X along the case edge, +Y toward the back, Z up, base underside on Z = 0.
Tilted frame (rotated about X): s = across the groove, front to back; t = up along the case.
"""
import math
from build123d import Axis, Pos, Rot, Part
from at070 import params as p
from at070.geom import box

_a = math.radians(p.tilt_deg)
SIN, COS = math.sin(_a), math.cos(_a)


def _com_rel(case_h):
    """COM Y relative to the groove origin (floor, front face of groove)."""
    return (p.groove_w / 2) * COS + (case_h / 2) * SIN


def groove_origin_y():
    """Place the groove so both orientations give symmetric COM offsets about the base center."""
    lo = _com_rel(min(p.outer_w, p.outer_h))
    hi = _com_rel(max(p.outer_w, p.outer_h))
    return -(lo + hi) / 2


def com_y(case_h):
    """Case center-of-mass projected on the base (Y), case height measured along the tilt."""
    return groove_origin_y() + _com_rel(case_h)


def base_y_range():
    return -p.stand_d / 2, p.stand_d / 2


def stand():
    hw = p.stand_w / 2
    base = box(-hw, hw, -p.stand_d / 2, p.stand_d / 2, 0, p.stand_base_t)
    base = base.fillet(p.stand_corner_r, base.edges().filter_by(Axis.Z))

    s0 = -p.lip_wall
    s1 = p.groove_w + p.rest_t
    wedge = box(-hw, hw, s0, s1, -200, 0)
    lip = box(-hw, hw, s0, 0, 0, p.lip_h)
    rest = box(-hw, hw, p.groove_w, s1, 0, 300)
    tilted = wedge + lip + rest
    z_o = p.stand_base_t + p.groove_w * SIN
    tilted = Pos(0, groove_origin_y(), z_o) * (Rot(X=-p.tilt_deg) * tilted)

    # keep only what sits over the base footprint, above the bed, below the back-rest top
    keep = box(-hw, hw, -p.stand_d / 2, p.stand_d / 2, 0, p.rest_top_z)
    keep = keep.fillet(p.stand_corner_r, keep.edges().filter_by(Axis.Z))
    tilted = tilted & keep
    return (base + tilted).clean()
