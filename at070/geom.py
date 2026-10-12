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
