"""Front shell: deep tray holding the panel, panel drops in from the back."""
import math
from build123d import Align, Axis, Cylinder, Pos, Rot, Part, Solid, Wire, Face, Vector
from at070 import params as p
from at070.geom import box, rbox


def outer_solid(z0, z1):
    """Rounded-corner outer outline prism from z0 to z1."""
    b = box(p.outer_x0, p.outer_x1, p.outer_y0, p.outer_y1, z0, z1)
    return b.fillet(p.corner_r, b.edges().filter_by(Axis.Z))


def clip_positions():
    """(wall, tangential coordinate) for each clip; wall in 'top','bottom','left','right'."""
    out = [("top", x) for x in p.clip_top_xs] + [("bottom", x) for x in p.clip_bottom_xs]
    out += [("left", p.clip_side_y), ("right", p.clip_side_y)]
    return out


def wall_frame(wall_name):
    """Return (angle about Z, outer-normal-anchor point (x,y) function of tangential t)
    for a clip whose outward direction is the given wall's outward normal.
    Anchor = pocket inner face position at tangential t."""
    if wall_name == "right":
        return 0.0, lambda t: (p.pocket_x1, t)
    if wall_name == "top":
        return 90.0, lambda t: (t, p.pocket_y1)
    if wall_name == "left":
        return 180.0, lambda t: (p.pocket_x0, t)
    return 270.0, lambda t: (t, p.pocket_y0)


def _slot(wall_name, t):
    ang, anchor = wall_frame(wall_name)
    ax, ay = anchor(t)
    hw = p.clip_width / 2 + p.slot_clearance
    z0 = p.z_rim - p.clip_length - p.slot_clearance
    z1 = p.z_rim - p.clip_length + p.hook_height + p.slot_top_clearance
    # local frame: u outward from inner face, v tangential; cut through wall (+0.5 overshoot)
    s = box(-0.5, p.wall + 0.5, -hw, hw, z0, z1)
    return Pos(ax, ay, 0) * (Rot(Z=ang) * s)


def front_shell():
    shell = outer_solid(-p.front_thickness, p.z_rim)
    front_edges = shell.edges().filter_by_position(Axis.Z, -p.front_thickness - 1e-3,
                                                   -p.front_thickness + 1e-3)
    shell = shell.fillet(p.front_fillet, front_edges)

    # panel pocket
    shell -= rbox(p.pocket_x0, p.pocket_x1, p.pocket_y0, p.pocket_y1, 0, p.z_rim + 1, p.pocket_r)

    # locating blocks (overlap 0.5 into walls to fuse)
    h = p.lb_h
    hw = p.lb_w / 2
    for x in p.lb_bottom_xs:
        shell += box(x - hw, x + hw, p.pocket_y0 - 0.5, p.lb_bottom_y, 0, h)
    for y in p.lb_left_ys:
        shell += box(p.pocket_x0 - 0.5, p.lb_left_x, y - hw, y + hw, 0, h)
    for x in p.lb_top_xs:
        shell += box(x - hw, x + hw, p.lb_top_y, p.pocket_y1 + 0.5, 0, h)

    # window with front chamfer
    wx0 = p.aa_x0 - p.window_margin
    wx1 = p.aa_x0 + p.aa_w + p.window_margin
    wy0 = p.aa_y0 - p.window_margin
    wy1 = p.aa_y0 + p.aa_h + p.window_margin
    shell -= box(wx0, wx1, wy0, wy1, -p.front_thickness - 1, 0.5)
    c = p.window_chamfer
    zf = -p.front_thickness

    def rect(x0, x1, y0, y1, z):
        return Wire.make_polygon([Vector(x0, y0, z), Vector(x1, y0, z),
                                  Vector(x1, y1, z), Vector(x0, y1, z)])
    # extend the cone 1 mm in front of the face to avoid coplanar faces
    cone = Solid.make_loft([rect(wx0 - c - 1, wx1 + c + 1, wy0 - c - 1, wy1 + c + 1, zf - 1),
                            rect(wx0, wx1, wy0, wy1, zf + c)])
    shell -= cone

    # HDMI alcove cut (open from rim down to the panel back; the lid's alcove fills it)
    hw_n = p.hdmi_notch_w / 2
    shell -= box(p.hdmi_x - hw_n, p.hdmi_x + hw_n, p.pocket_y1 - 0.5, p.outer_y1 + 1,
                 p.hdmi_notch_z0, p.z_rim + 1)

    # power notch with round bottom
    r = p.power_notch_w / 2
    shell -= box(p.power_x - r, p.power_x + r, p.pocket_y1 - 0.5, p.outer_y1 + 1,
                 p.power_z, p.z_rim + 1)
    y0c = p.pocket_y1 - 0.5
    cyl = Cylinder(r, p.outer_y1 + 1 - y0c, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cyl = Pos(p.power_x, y0c, p.power_z) * (Rot(X=-90) * cyl)
    shell -= cyl

    # clip slots
    for w, t in clip_positions():
        shell -= _slot(w, t)

    return shell.clean()
