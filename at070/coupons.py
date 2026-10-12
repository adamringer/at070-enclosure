"""Fit-test coupons (assembled coordinates; build.py orients them for printing)."""
from build123d import Pos
from at070 import kickstand, params as p
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


def _hinge_origin():
    """Canonical kickstand frame placed on the lid back, model frame."""
    return Pos(0, 0, p.z_lid_top)


def coupon_hinge_lid():
    """Flat piece of lid plate with the slots for both hinge blocks."""
    x0, x1 = p.coupon_hinge_x
    y0, y1 = p.coupon_hinge_y
    plate = box(x0, x1, y0, y1, p.z_rim, p.z_lid_top)
    for bx in kickstand.block_x0s(p.coupon_hinge_w):
        for sb in kickstand.slot_boxes(bx):
            plate -= _hinge_origin() * sb
    return plate.clean()


def coupon_hinge_flap(opening=0.0):
    """Short flap: plate, knuckle with the notched cam (main-flap notches), a hole in each end."""
    f = kickstand.flap(p.coupon_hinge_w, p.coupon_hinge_len, p.ks_main_notches)
    return _hinge_origin() * kickstand.pose_flap(f, opening)


def coupon_hinge_blocks(tip=True):
    """(plain block, spring block) in place on the coupon lid piece."""
    xp, xs = kickstand.block_x0s(p.coupon_hinge_w)
    return (_hinge_origin() * kickstand.hinge_block(xp),
            _hinge_origin() * kickstand.hinge_block(xs, spring=True, tip=tip))
