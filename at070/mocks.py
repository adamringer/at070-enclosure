"""Non-printed reference solids in assembled positions."""
import math
from build123d import Cylinder, Pos, Rot, Axis, Align
from at070 import params as p
from at070.geom import box


def panel():
    return box(-p.panel_w / 2, p.panel_w / 2, -p.panel_h / 2, p.panel_h / 2, 0, p.panel_t)


def board_keepout():
    m = p.board_keepout_margin
    return box(p.board_x0 - m, p.board_x1 + m, p.board_y0 - m, p.board_y1 + m,
               p.panel_t, p.board_top_z)


def _ycyl(d, x, z, y0, y1):
    c = Cylinder(d / 2, y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    c = Rot(X=-90) * c      # axis Z -> +Y, starts at y=0
    return Pos(x, y0, z) * c


def hdmi_plug():
    body = box(p.hdmi_x - p.plug_w / 2, p.hdmi_x + p.plug_w / 2, p.hdmi_mouth_y,
               p.hdmi_mouth_y + p.plug_len, p.hdmi_z - p.plug_t / 2, p.hdmi_z + p.plug_t / 2)
    y1 = p.hdmi_mouth_y + p.plug_len
    cable = _ycyl(p.plug_cable_d, p.hdmi_x, p.hdmi_z, y1 - 1.0, y1 + p.plug_cable_len)
    return body + cable


def power_cable():
    cable = _ycyl(p.power_cable_d, p.power_x, p.power_z, p.power_cable_y0, p.power_cable_y1)
    shrink = _ycyl(p.power_shrink_d, p.power_x, p.power_z, p.power_shrink_y0, p.power_shrink_y1)
    return cable + shrink
