"""Fit-test coupons (assembled coordinates; build.py orients them for printing)."""
from at070 import params as p
from at070.front_shell import front_shell
from at070.geom import box
from at070.lid import lid


def _top_box():
    x0, x1, y0, y1 = p.coupon_box
    return box(x0, x1, y0, y1, -p.front_thickness - 1, p.z_lid_top + 1)


def coupon_fit_frame():
    """Shell cut at coupon_fit_z, except the top-edge section (coupon_box), which keeps full
    height with the HDMI/power notches and one clip slot for the lid coupon to snap onto."""
    low = box(p.outer_x0 - 1, p.outer_x1 + 1, p.outer_y0 - 1, p.outer_y1 + 1,
              -p.front_thickness - 1, p.coupon_fit_z)
    return (front_shell() & (low + _top_box())).clean()


def coupon_top_edge_lid():
    return (lid() & _top_box()).clean()
