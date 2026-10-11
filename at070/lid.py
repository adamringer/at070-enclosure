"""Lid: back plate with locating lip, six snap clips and four panel press ribs."""
from build123d import Axis, Face, Part, Pos, Rot, Solid, Vector, Wire
from at070 import params as p
from at070.front_shell import clip_positions, outer_solid, wall_frame
from at070.geom import box

EMBED = 0.5  # features extend this far into the plate to fuse reliably


def clip_strain():
    """Cantilever max strain = 1.5 * t * y / L^2."""
    return 1.5 * p.clip_thickness * p.hook_overlap / p.clip_length ** 2


def _clip_template():
    """One clip in a local frame: u (X) outward from the wall inner face, v (Y) tangential,
    Z as assembled. Outer face of the clip is at u = -clip_gap."""
    zt = p.z_rim - p.clip_length                 # tip Z
    uo = -p.clip_gap                             # clip outer face
    ui = uo - p.clip_thickness                   # clip inner face
    ztop = p.z_rim + EMBED
    pts = [(ui, zt), (uo, zt),
           (uo + p.hook_lead, zt + p.hook_lead),     # 45 deg lead-in
           (uo + p.hook_overlap, zt + p.hook_lead),
           (uo + p.hook_overlap, zt + p.hook_height),  # catch face
           (uo, zt + p.hook_height),
           (uo, ztop), (ui, ztop)]
    face = Face(Wire.make_polygon([Vector(u, 0, z) for u, z in pts]))
    s = Solid.extrude(face, Vector(0, p.clip_width, 0))
    return Pos(0, -p.clip_width / 2, 0) * s


def _place(shape, wall_name, t):
    ang, anchor = wall_frame(wall_name)
    ax, ay = anchor(t)
    return Pos(ax, ay, 0) * (Rot(Z=ang) * shape)


def clips():
    tmpl = _clip_template()
    res = None
    for w, t in clip_positions():
        c = _place(tmpl, w, t)
        res = c if res is None else res + c
    return res


def press_ribs():
    """Four L-shaped corner ribs, tips at panel back + press_gap."""
    z0 = p.panel_t + p.press_gap
    z1 = p.z_rim + EMBED
    res = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * (p.panel_w / 2 - p.rib_inset)
            cy = sy * (p.panel_h / 2 - p.rib_inset)
            x_in = cx - sx * p.rib_leg
            y_in = cy - sy * p.rib_leg
            xt = cx - sx * p.rib_t
            yt = cy - sy * p.rib_t
            leg_x = box(min(cx, x_in), max(cx, x_in), min(cy, yt), max(cy, yt), z0, z1)
            leg_y = box(min(cx, xt), max(cx, xt), min(cy, y_in), max(cy, y_in), z0, z1)
            r = leg_x + leg_y
            res = r if res is None else res + r
    return res.clean()


def _lip():
    z0, z1 = p.lip_z0, p.z_rim + EMBED
    a = p.lip_inset
    b = p.lip_inset + p.lip_t
    ring = (box(p.pocket_x0 + a, p.pocket_x1 - a, p.pocket_y0 + a, p.pocket_y1 - a, z0, z1)
            - box(p.pocket_x0 + b, p.pocket_x1 - b, p.pocket_y0 + b, p.pocket_y1 - b, z0 - 1, z1 + 1))
    cz0, cz1 = z0 - 1, p.z_rim   # cutters stop at the plate face
    # notch interruptions
    for x, w in ((p.hdmi_x, p.hdmi_notch_w), (p.power_x, p.power_notch_w)):
        hw = (w + p.lip_notch_extra) / 2
        ring -= box(x - hw, x + hw, p.pocket_y1 - 4, p.pocket_y1 + 1, cz0, cz1)
    # clip interruptions
    cut = box(-4.0, 1.0, -(p.clip_width + p.lip_clip_extra) / 2,
              (p.clip_width + p.lip_clip_extra) / 2, cz0, cz1)
    for w, t in clip_positions():
        ring -= _place(cut, w, t)
    # rib clearance
    e = p.lip_rib_extra
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * (p.panel_w / 2 - p.rib_inset)
            cy = sy * (p.panel_h / 2 - p.rib_inset)
            xa, xb = sorted((cx, cx - sx * p.rib_leg))
            ya, yb = sorted((cy, cy - sy * p.rib_leg))
            ring -= box(xa - e, xb + e, ya - e, yb + e, cz0, cz1)
    return ring


def hdmi_alcove():
    """Open alcove at the HDMI socket: two side walls, a back wall with a slot for the plug body,
    and a floor, all hanging from the lid. The lid plate is cut away over it (see lid())."""
    x, hi, ho = p.hdmi_x, p.alcove_hw_in, p.alcove_hw_out
    y0, y1 = p.alcove_y0, p.outer_y1
    z0, z1 = p.alcove_z0, p.z_rim + EMBED
    walls = (box(x - ho, x - hi, y0, y1, z0, z1) + box(x + hi, x + ho, y0, y1, z0, z1)
             + box(x - ho, x + ho, y0, y1, z0, z0 + p.alcove_wall)
             + box(x - ho, x + ho, y0, y0 + p.alcove_wall, z0, z1))
    c = p.plug_slot_clear
    slot = box(x - p.plug_w / 2 - c, x + p.plug_w / 2 + c, y0 - 1, y0 + p.alcove_wall + 1,
               p.hdmi_z - p.plug_t / 2 - c, p.z_rim)
    return walls - slot


def lid():
    plate = outer_solid(p.z_rim, p.z_lid_top)
    back = plate.edges().filter_by_position(Axis.Z, p.z_lid_top - 1e-3, p.z_lid_top + 1e-3)
    plate = plate.fillet(p.edge_fillet, back)
    out = plate + _lip() + clips() + press_ribs()
    # open the lid over the HDMI alcove (after the lip, whose top fuses into the plate)
    out -= box(p.hdmi_x - p.alcove_hw_in, p.hdmi_x + p.alcove_hw_in,
               p.alcove_y0 + p.alcove_wall, p.outer_y1 + 1, p.z_rim - 1, p.z_lid_top + 1)
    out += hdmi_alcove()
    return out.clean()
