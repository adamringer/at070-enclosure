"""Kickstand: clearances, rotation range, stability, strain and printability."""
import math

import pytest
from at070 import coupons, kickstand as ks, mocks, params as p
from at070.build import printable_parts
from at070.front_shell import front_shell
from at070.geom import box
from at070.lid import lid

MAIN_LAST = max(p.ks_main_notches)
PROP_OPEN = max(p.ks_prop_notches)
MOCKS = ["panel", "board_keepout", "hdmi_plug", "power_cable"]


def overlap(a, b):
    r = a & b
    return 0.0 if r is None else r.volume


def sweep_angles(last):
    n = int(last // p.ks_sweep_step)
    return [i * p.ks_sweep_step for i in range(n + 1)] + ([last] if last % p.ks_sweep_step else [])


@pytest.fixture(scope="module")
def shell():
    return front_shell()


@pytest.fixture(scope="module")
def lid_part():
    return lid()


@pytest.fixture(scope="module")
def closed():
    return ks.all_parts()


@pytest.fixture(scope="module")
def printable():
    return printable_parts()


# ---- constraint 1: closed state, assembled on the lid

@pytest.mark.parametrize("name", ["main_flap", "main_block_plain", "main_block_spring",
                                  "prop_flap", "prop_block_plain", "prop_block_spring"])
def test_closed_no_interference(closed, shell, lid_part, name):
    part = closed[name]
    assert part.is_valid and len(part.solids()) == 1
    assert overlap(part, lid_part) < 0.01
    assert overlap(part, shell) < 0.01
    for m in MOCKS:
        assert overlap(part, getattr(mocks, m)()) < 0.01


def test_closed_kickstand_parts_do_not_touch_each_other(closed):
    names = list(closed)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert overlap(closed[a], closed[b]) < 0.05, (a, b)


def test_slots_only_remove_plate(lid_part):
    """Each slot removes exactly slot area x plate thickness (nothing from lip, ribs, clips)."""
    plain = lid(slots=False)
    removed = plain.volume - lid_part.volume
    expected = 0.0
    for c in ks.slot_cutters():
        bb = c.bounding_box()
        expected += (bb.size.X * bb.size.Y) * p.lid_plate_t
    assert removed == pytest.approx(expected, abs=0.5)


def test_slot_and_leg_clearances():
    """Legs (slot footprint grown by the clearance) stay clear of the board keep-out, the lip
    zone, press ribs, clips and the alcove. Checked on the block's leg envelope in XY."""
    plain = lid(slots=False)
    for c in ks.slot_cutters():
        bb = c.bounding_box()
        env = box(bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, p.z_rim - 2.5, p.z_rim)
        assert overlap(env, mocks.board_keepout()) < 0.01
        assert overlap(env, plain) < 0.01          # lip, ribs, clips, alcove live under the plate
        gap = 0.3
        env2 = box(bb.min.X - gap, bb.max.X + gap, bb.min.Y - gap, bb.max.Y + gap,
                   p.z_rim - 2.5, p.z_rim)
        assert overlap(env2, plain) < 0.01


def test_hdmi_alcove_open_with_kickstand(closed):
    x, hw = p.hdmi_x, p.plug_w / 2
    y0 = p.alcove_y0 + p.alcove_wall + 0.1
    top = box(x - hw, x + hw, y0, p.outer_y1 + 1, p.hdmi_z + p.plug_t / 2, p.z_lid_top + 1)
    states = [closed, ks.all_parts(MAIN_LAST, PROP_OPEN)]
    for st in states:
        for name, part in st.items():
            assert overlap(part, top) < 0.01, name


def test_kickstand_inside_lid_outline(closed):
    e = p.edge_fillet + 0.5
    for name, part in closed.items():
        bb = part.bounding_box()
        assert bb.min.X >= p.outer_x0 + e and bb.max.X <= p.outer_x1 - e, name
        assert bb.min.Y >= p.outer_y0 + e and bb.max.Y <= p.outer_y1 - e, name


def test_prop_clearances(closed):
    """Prop at least 3 mm from the alcove opening and from the main flap's hinge parts."""
    for name, part in closed.items():
        if not name.startswith("prop"):
            continue
        assert part.bounding_box().min.X >= p.hdmi_x + p.alcove_hw_out + 3.0, name
        for mname, m in closed.items():
            if mname.startswith("main"):
                a, b = part.bounding_box(), m.bounding_box()
                gx = max(a.min.X - b.max.X, b.min.X - a.max.X)
                gy = max(a.min.Y - b.max.Y, b.min.Y - a.max.Y)
                assert max(gx, gy) >= 3.0, (name, mname)


def test_hinge_line_height(closed, printable):
    """Everything along the hinge line (knuckle, cam, blocks, leaf) stays within ~8.5 mm of the
    lid back, and no block is taller than the knuckle."""
    assert 2 * p.ks_knuckle_r <= 8.5 and p.ks_gap + 2 * p.ks_knuckle_r <= 8.5
    b = ks.hinge_block(0.0, spring=True).bounding_box()
    assert b.max.Z <= p.ks_gap + 2 * p.ks_knuckle_r
    for name, part in closed.items():
        if name.endswith("flap"):
            continue
        assert part.bounding_box().max.Z <= p.z_lid_top + 8.5, name
    for name in ("main_flap", "prop_flap"):
        assert closed[name].bounding_box().max.Z <= p.z_lid_top + 8.5


def test_detent_holds_the_case():
    """Estimated detent holding torque vs the torque the case weight puts on the flap."""
    rows = ks.detent_table()
    assert len(rows) == len(p.ks_main_notches) - 1 + len(p.ks_prop_notches) - 1
    for r in rows:
        assert r["hold"] >= r["load"], r


# ---- constraint 2: rotation range

@pytest.mark.parametrize("which,last", [("main", MAIN_LAST), ("prop", PROP_OPEN)])
def test_flap_sweep_clear(shell, lid_part, closed, which, last):
    other = "prop" if which == "main" else "main"
    for a in sweep_angles(last):
        parts = (ks.main_parts if which == "main" else ks.prop_parts)(a, tip=False)
        f = parts["flap"]
        assert overlap(f, lid_part) < 0.01, a
        assert overlap(f, shell) < 0.01, a
        assert overlap(f, parts["block_plain"]) < 0.01, a
        assert overlap(f, parts["block_spring"]) < 0.01, a
        for n, part in closed.items():
            if n.startswith(other):
                assert overlap(f, part) < 0.01, (a, n)


def test_detent_clicks_in_every_notch():
    """The spring tip rests in each notch without interference and bites into the cam between."""
    for which, notches in (("main", p.ks_main_notches), ("prop", p.ks_prop_notches)):
        mk = ks.main_parts if which == "main" else ks.prop_parts
        for a in notches:
            parts = mk(a)
            assert overlap(parts["flap"], parts["block_spring"]) < 0.05, (which, a)
        ns = sorted(notches)
        for a, b in zip(ns, ns[1:]):
            mid = (a + b) / 2
            parts = mk(mid)
            assert overlap(parts["flap"], parts["block_spring"]) > 0.3, (which, mid)


def test_notch_pitch_fits_cam():
    for notches in (p.ks_main_notches, p.ks_prop_notches):
        ns = sorted(notches)
        for a, b in zip(ns, ns[1:]):
            assert b - a >= ks.min_notch_pitch_deg()


# ---- constraints 3 and 4: stability

def test_landscape_tilt_and_com():
    table = ks.main_table()
    tilts = [t["tilt"] for t in table]
    assert tilts[0] >= p.ks_tilt_min and tilts[0] <= p.ks_tilt_min + 1.5
    assert tilts[-1] >= p.ks_tilt_max
    steps = [b - a for a, b in zip(tilts, tilts[1:])]
    assert min(steps) >= 5.0 and max(steps) <= 12.0
    for t in table:
        assert t["margin_contact"] >= p.ks_com_margin, t
        assert t["margin_foot"] >= p.ks_com_margin, t


def test_first_notch_is_smallest_opening_with_enough_tilt():
    first = ks.main_table()[0]
    below = ks.support("landscape", first["opening"] - 1.0)
    assert below is None or below["tilt"] < p.ks_tilt_min or below["margin_contact"] < p.ks_com_margin


def test_portrait_lean_and_com():
    s = ks.prop_state()
    assert p.ks_lean_min <= s["tilt"] <= p.ks_lean_max
    assert s["margin_contact"] >= p.ks_com_margin
    assert s["margin_foot"] >= p.ks_com_margin


def _lowest(solid, up):
    return min(up[0] * v.X + up[1] * v.Y + up[2] * v.Z for v in solid.vertices())


def test_analytic_foot_matches_solid():
    """The 2D free-end model agrees with the actual posed flap solid (lowest point along the
    case's 'up' direction, relative to the lowest point of the contact fillet)."""
    for orient, mk, notches in (("landscape", ks.main_parts, p.ks_main_notches),
                                ("portrait", ks.prop_parts, p.ks_prop_notches)):
        for a in notches:
            if a == 0:
                continue
            s = ks.support(orient, a)
            r = math.radians(s["tilt"])
            up = (0, math.cos(r), -math.sin(r)) if orient == "landscape" else (-math.cos(r), 0, -math.sin(r))
            flap = mk(a)["flap"]
            e = p.edge_fillet
            ref = (up[1] if orient == "landscape" else up[0]) * s["contact"][0] + up[2] * s["contact"][1] - e
            assert _lowest(flap, up) - ref == pytest.approx(0.0, abs=0.05), (orient, a)


# ---- constraint 5: strain

def test_leaf_spring_strain():
    assert ks.leaf_strain() <= p.ks_leaf_strain_max


def test_notch_flank_steepness():
    assert 55.0 <= p.ks_flank_deg <= 65.0
    # the tip fits in the notch: seated tip drop equals the notch depth
    drop = (p.ks_knuckle_r + p.ks_tip_r) - ks.tip_seated_dist()
    assert drop == pytest.approx(p.ks_notch_depth, abs=1e-9)


def test_snap_leg_strain():
    assert ks.leg_strain() <= p.ks_leg_strain_max


# ---- constraint 6: printability

@pytest.mark.parametrize("name", ["kickstand_flap", "kickstand_prop", "hinge_block",
                                  "hinge_block_spring", "coupon_hinge_lid", "coupon_hinge_flap"])
def test_kickstand_part_printable(printable, name):
    part = printable[name]
    assert part.is_valid and len(part.solids()) == 1
    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert bb.size.X <= p.bed_limit and bb.size.Y <= p.bed_limit


def _slice_area(part, z, t=0.2):
    bb = part.bounding_box()
    sl = part & box(bb.min.X - 1, bb.max.X + 1, bb.min.Y - 1, bb.max.Y + 1, z - t / 2, z + t / 2)
    return 0.0 if sl is None else sl.volume / t


def test_hinge_block_prints_without_supports(printable):
    """Printed standing on the block's outer end face, every layer of the block has the same
    profile (nothing hangs in the air); the pin (and the spring leaf) grow straight up from it,
    so the pin prints round."""
    bw, pl = p.ks_block_w, p.ks_pin_len
    pin_area = math.pi * (p.ks_pin_d / 2) ** 2
    plain = printable["hinge_block"]
    assert plain.bounding_box().size.Z == pytest.approx(bw + pl, abs=0.01)
    a = [_slice_area(plain, z) for z in (0.5, 2.0, bw - 0.5)]
    assert max(a) - min(a) < 0.5
    assert _slice_area(plain, bw + 1.0) == pytest.approx(pin_area, abs=0.5)
    assert _slice_area(plain, bw + 3.0) == pytest.approx(pin_area, abs=0.5)
    spring = printable["hinge_block_spring"]
    h = spring.bounding_box().size.Z
    block = [_slice_area(spring, z) for z in (0.5, 2.0, bw - 0.5)]
    assert max(block) - min(block) < 0.5
    up = [_slice_area(spring, z) for z in (bw + 1.0, bw + 3.0)]           # leaf + pin
    assert max(up) - min(up) < 0.5
    leaf = [_slice_area(spring, z) for z in (bw + pl + 0.5, bw + pl + 1.5)]
    assert max(leaf) - min(leaf) < 0.5
    assert h == pytest.approx(bw + p.ks_leaf_len, abs=0.01)


def test_flap_prints_flat_on_the_bed(printable):
    for name in ("kickstand_flap", "kickstand_prop", "coupon_hinge_flap"):
        part = printable[name]
        bb = part.bounding_box()
        assert bb.size.Z == pytest.approx(2 * p.ks_knuckle_r, abs=0.01)   # knuckle top; plate underside on the bed
        sl = part & box(bb.min.X - 1, bb.max.X + 1, bb.min.Y - 1, bb.max.Y + 1, 0.0, 0.01)
        assert sl is not None and sl.volume > 0.1


# ---- pins and holes

def _pin_x_ranges(width):
    """X ranges (canonical) of the two hinge pins."""
    xp, xs = ks.block_x0s(width)
    return ((xp + p.ks_block_w, xp + p.ks_block_w + p.ks_pin_len), (xs - p.ks_pin_len, xs))


def test_pins_fit_holes_with_clearance_at_every_notch():
    """Each pin sits inside its blind hole with ks_pin_hole_clear all round: a cylinder just
    under the hole diameter does not touch the flap, one just over does, and the pin itself
    never touches the flap, at every notch angle and the full sweep."""
    from at070.geom import cyl_x
    width = p.ks_main_w
    angles = sorted(set(list(p.ks_main_notches) + sweep_angles(MAIN_LAST)))
    for a in angles:
        parts = ks.main_parts(a, tip=False)
        flap = ks.pose_flap(ks.flap(width, p.ks_main_len, p.ks_main_notches), a)
        for (xa, xb) in _pin_x_ranges(width):
            r = p.ks_pin_d / 2 + p.ks_pin_hole_clear
            inside = cyl_x(0, p.ks_axis_z, r - 0.01, xa + p.ks_ax_gap, xb)
            outside = cyl_x(0, p.ks_axis_z, r + 0.01, xa + p.ks_ax_gap, xb)
            assert overlap(flap, inside) < 0.01, a
            assert overlap(flap, outside) > 0.05, a
        assert overlap(parts["flap"], parts["block_plain"]) < 0.01, a
        assert overlap(parts["flap"], parts["block_spring"]) < 0.01, a


def test_pin_engagement_and_hole_depth():
    assert p.ks_pin_len - p.ks_ax_gap == pytest.approx(p.ks_pin_engage)
    assert p.ks_hole_depth == pytest.approx(p.ks_pin_engage + p.ks_hole_extra)
    assert p.ks_hole_d == pytest.approx(p.ks_pin_d + 2 * p.ks_pin_hole_clear)


def test_hole_walls():
    radial, axial = ks.hole_wall()
    assert radial >= p.ks_hole_wall
    assert axial >= p.ks_hole_wall
    # the notch zone covers the spring tip
    face = p.ks_ax_gap + p.ks_cam_len
    assert p.ks_notch_x0 <= face - p.ks_leaf_len
    assert face - p.ks_leaf_len + p.ks_tip_len <= p.ks_notch_x0 + p.ks_notch_len


def test_teardrop_hole_point_up():
    f = ks.flap(p.ks_main_w, p.ks_main_len, p.ks_main_notches)
    hw = p.ks_main_w / 2
    r = p.ks_hole_d / 2
    za = p.ks_axis_z
    x = -hw + 1.0
    probe = lambda y, z: overlap(f, box(x - 0.2, x + 0.2, y - 0.05, y + 0.05, z - 0.05, z + 0.05))
    assert probe(0.0, za + r * math.sqrt(2) - 0.2) < 1e-6          # inside the point: empty
    assert probe(0.0, za - r + 0.1) < 1e-6                         # inside the bottom: empty
    assert probe(0.0, za + r * math.sqrt(2) + 0.2) > 1e-6          # beyond the point: solid
    assert probe(r * 1.3, za - 0.0) > 1e-6                         # beside the round part: solid


# ---- hinge coupon

def test_coupon_hinge_fits_and_clicks():
    lid_piece = coupons.coupon_hinge_lid()
    plain, spring = coupons.coupon_hinge_blocks(tip=False)
    assert overlap(plain, lid_piece) < 0.01 and overlap(spring, lid_piece) < 0.01
    assert overlap(plain, spring) < 0.01
    for a in sweep_angles(MAIN_LAST):
        f = coupons.coupon_hinge_flap(a)
        assert overlap(f, lid_piece) < 0.01, a
        assert overlap(f, plain) < 0.01, a
        assert overlap(f, spring) < 0.01, a
    plain, spring = coupons.coupon_hinge_blocks()
    for a in p.ks_main_notches:
        assert overlap(coupons.coupon_hinge_flap(a), spring) < 0.05, a
    x0, x1 = p.coupon_hinge_x
    y0, y1 = p.coupon_hinge_y
    bb = lid_piece.bounding_box()
    assert (bb.size.X, bb.size.Y) == pytest.approx((x1 - x0, y1 - y0))
    for part in (plain, spring, coupons.coupon_hinge_flap(0.0)):
        b = part.bounding_box()
        assert b.min.X >= x0 and b.max.X <= x1 and b.min.Y >= y0 and b.max.Y <= y1
