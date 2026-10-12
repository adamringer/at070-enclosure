"""Small geometry helpers."""
from build123d import Box, Cylinder, Plane, Polygon, Pos, Rot, extrude


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from min/max coordinates."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def rbox(x0, x1, y0, y1, z0, z1, r):
    """Box with its four vertical (Z) edges rounded to radius r."""
    from build123d import Axis
    b = box(x0, x1, y0, y1, z0, z1)
    return b.fillet(r, b.edges().filter_by(Axis.Z)) if r > 0 else b


def prism_x(pts, x0, x1):
    """Polygon given as (Y, Z) points (either winding), extruded along X from x0 to x1."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts = pts[::-1]          # extrusion goes along the plane normal only for CCW points
    return extrude(Plane.YZ.offset(x0) * Polygon(*pts, align=None), amount=x1 - x0)


def cyl_x(y, z, r, x0, x1):
    """Cylinder with its axis parallel to X through (y, z), from x0 to x1."""
    return Pos((x0 + x1) / 2, y, z) * (Rot(Y=90) * Cylinder(r, abs(x1 - x0)))


def c_socket(pin_d, y, z, x0, x1, mouth, reach, pin_clear, snap_interf, chamfer):
    """Cutter for a snap-in C-socket along X, opening toward +Z. Hole diameter
    pin_d + 2*pin_clear, with an entry slot (width pin_d - 2*snap_interf) leaving the hole
    toward +Z and a 45 deg lead-in of size `chamfer` at the mouth. `mouth` = distance from the
    hole axis to the block surface along +Z, measured at the slot edge. `reach` = how far the
    cutter extends along +Z (curved surfaces need more than `mouth`)."""
    hw = (pin_d - 2 * snap_interf) / 2
    w_top = hw + (reach - (mouth - chamfer))      # the lead-in continues at 45 deg to the top
    uv = [(-hw, 0), (hw, 0), (hw, mouth - chamfer), (w_top, reach), (-w_top, reach),
          (-hw, mouth - chamfer)]
    pts = [(y + u, z + v) for u, v in uv]
    return cyl_x(y, z, pin_d / 2 + pin_clear, x0, x1) + prism_x(pts, x0, x1)
