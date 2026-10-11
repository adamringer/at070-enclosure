import math

import pytest
from build123d import Axis
from at070 import coupons, mocks, params as p
from at070.build import printable_parts
from at070.front_shell import front_shell
from at070.geom import box
from at070.lid import clip_strain, lid, press_ribs
from at070 import stand as st


@pytest.fixture(scope="module")
def shell():
    return front_shell()


@pytest.fixture(scope="module")
def lid_part():
    return lid()


@pytest.fixture(scope="module")
def printable():
    return printable_parts()


def overlap(a, b):
    r = a & b
    if r is None:
        return 0.0
    return r.volume


@pytest.mark.parametrize("name", ["front_shell", "lid", "stand_base", "stand_cradle",
                                  "stand_strut", "coupon_fit_frame", "coupon_top_edge_lid"])
def test_single_valid_solid_fits_and_on_bed(printable, name):
    part = printable[name]
    assert part.is_valid
    assert len(part.solids()) == 1
    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert bb.size.X <= 250 and bb.size.Y <= 250 and bb.size.Z <= 250


def test_unoriented_parts_single_solid(shell, lid_part):
    for s in (shell, lid_part):
        assert s.is_valid and len(s.solids()) == 1


@pytest.mark.parametrize("mock", ["panel", "hdmi_plug", "power_cable"])
def test_shell_no_interference(shell, mock):
    assert overlap(shell, getattr(mocks, mock)()) < 0.01


@pytest.mark.parametrize("mock", ["panel", "board_keepout", "hdmi_plug", "power_cable"])
def test_lid_no_interference(lid_part, mock):
    assert overlap(lid_part, getattr(mocks, mock)()) < 0.01


def test_shell_vs_lid(shell, lid_part):
    assert overlap(shell, lid_part) < 0.01


def test_window_contains_aa_and_inside_panel():
    wx0, wx1 = p.aa_x0 - p.window_margin, p.aa_x0 + p.aa_w + p.window_margin
    wy0, wy1 = p.aa_y0 - p.window_margin, p.aa_y0 + p.aa_h + p.window_margin
    assert wx0 <= p.aa_x0 and wx1 >= p.aa_x0 + p.aa_w
    assert wy0 <= p.aa_y0 and wy1 >= p.aa_y0 + p.aa_h
    assert wx0 > -p.panel_w / 2 and wx1 < p.panel_w / 2
    assert wy0 > -p.panel_h / 2 and wy1 < p.panel_h / 2


def test_window_centered_in_outline(shell):
    # section the front plate just behind the chamfer (Z -0.5..-0.1) and read its wires
    sl = shell & box(p.outer_x0 - 1, p.outer_x1 + 1, p.outer_y0 - 1, p.outer_y1 + 1, -0.5, -0.1)
    face = sl.faces().filter_by(Axis.Z).sort_by(Axis.Z)[0]   # lowest-Z planar face
    ob = face.outer_wire().bounding_box()
    ib = face.inner_wires()[0].bounding_box()
    assert abs((ib.min.X + ib.max.X) / 2 - (ob.min.X + ob.max.X) / 2) < 0.01
    assert abs((ib.min.Y + ib.max.Y) / 2 - (ob.min.Y + ob.max.Y) / 2) < 0.01
    assert abs((ib.min.X - ob.min.X) - (ob.max.X - ib.max.X)) < 0.01
    assert abs((ib.min.Y - ob.min.Y) - (ob.max.Y - ib.max.Y)) < 0.01
    # window matches the AA + margin
    assert abs(ib.size.X - (p.aa_w + 2 * p.window_margin)) < 0.01
    assert abs((ib.min.X + ib.max.X) / 2 - p.aa_cx) < 0.01
    assert abs((ib.min.Y + ib.max.Y) / 2 - p.aa_cy) < 0.01


def test_press_rib_tips():
    zmin = press_ribs().bounding_box().min.Z
    assert abs(zmin - (p.panel_t + p.press_gap)) < 1e-6


def test_clip_strain():
    assert clip_strain() <= p.clip_strain_max


@pytest.fixture(scope="module")
def base():
    return st.stand_base()


@pytest.fixture(scope="module")
def cradle():
    return st.stand_cradle()


@pytest.fixture(scope="module")
def strut():
    return st.stand_strut()


THETAS = [5.0 * i for i in range(10)]
ORIENTATIONS = [True, False]        # landscape, portrait


def test_stand_params_sane():
    assert p.cradle_w < p.outer_h
    assert p.groove_w >= p.case_depth + 0.6
    assert p.pivot_pin_t == pytest.approx(-p.cradle_floor_t + p.pivot_pin_r)
    assert st.notch_angles() == THETAS


def test_stand_notch_spacing():
    """Constraint 1."""
    ys = st.notch_ys()
    assert len(ys) == len(THETAS)
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    assert min(gaps) >= 2 * p.notch_r + p.notch_min_gap


@pytest.mark.parametrize("theta", THETAS)
def test_stand_no_interference(base, cradle, strut, theta):
    """Constraint 2: parts pairwise, and the case box (both orientations) vs base and strut."""
    c = st.cradle_pose(theta)
    s = st.strut_pose(theta)
    assert overlap(base, c) < 0.01
    assert overlap(base, s) < 0.01
    assert overlap(c, s) < 0.01
    for land in ORIENTATIONS:
        cb = st.case_pose(theta, land)
        assert overlap(cb, base) < 0.01
        assert overlap(cb, s) < 0.01


@pytest.mark.parametrize("land", ORIENTATIONS)
def test_stand_case_clears_towers(land):
    """The case passes over the towers: radius from the pivot axis is preserved by the tilt."""
    s0 = p.cradle_s_total - p.cradle_rest_t - p.case_depth
    s1 = p.cradle_s_total - p.cradle_rest_t
    h = p.outer_h if land else p.outer_w
    ns = min(max(p.pivot_pin_s, s0), s1)
    nt = min(max(p.pivot_pin_t, 0.0), h)
    r = math.hypot(ns - p.pivot_pin_s, nt - p.pivot_pin_t)
    assert r >= st.tower_r() + p.tower_case_gap


def test_stand_strut_folds_against_rest(cradle, strut):
    folded = st.strut_folded_pose()
    assert overlap(st.cradle_pose(0.0), folded) < 0.01
    # and it lies behind the rest, not through the floor
    assert folded.bounding_box().min.Y > p.cradle_s_total - p.pivot_pin_s - 1e-6


@pytest.mark.parametrize("theta", THETAS)
@pytest.mark.parametrize("land", ORIENTATIONS)
def test_stand_com_over_base(theta, land):
    """Constraint 3 (COM clear of base front/back edges) and 4 (strut in compression)."""
    y0, y1 = st.base_y_range()
    y, _ = st.case_com(theta, land)
    assert y - y0 >= p.com_min_edge
    assert y1 - y >= p.com_min_edge
    assert y > 0.0                      # behind the pivot axis (Y = 0)


@pytest.mark.parametrize("theta", THETAS)
def test_stand_foot_in_notch(theta):
    ys = st.notch_ys()
    fy, fz = st.foot_axis(theta)
    assert abs(fy - ys[THETAS.index(theta)]) < 0.05
    assert abs(fz - st.foot_z()) < 0.05
    # the posed strut's foot cylinder: its bbox bottom sits one foot radius below the axis
    # only for a horizontal bar, so check the axis through the bar's pin-to-foot distance
    py, pz = st.strut_pin_axis(theta)
    assert abs(math.hypot(fy - py, fz - pz) - p.strut_len) < 0.05


@pytest.mark.parametrize("theta", THETAS)
def test_stand_posed_foot_matches_notch(strut, theta):
    """Find the foot in the posed solid: the lowest point must be foot_r below the foot axis
    (the foot is the lowest feature)."""
    s = st.strut_pose(theta)
    fy, fz = st.foot_axis(theta)
    bb = s.bounding_box()
    assert abs(bb.min.Z - (fz - p.foot_r)) < 0.05


def test_stand_pivot_clearance_at_max_tilt():
    assert st.lowest_cradle_z(p.tilt_max_deg) >= p.stand_base_t + p.swing_clearance - 1e-9
    low = st.cradle_pose(p.tilt_max_deg).bounding_box().min.Z
    assert low >= p.stand_base_t + p.swing_clearance - 0.02   # 0.02: pin flat sits 0.015 high
    # and pivot_z is the smallest such height: lowering it would violate the clearance
    assert st.lowest_cradle_z(p.tilt_max_deg) - 0.01 < p.stand_base_t + p.swing_clearance + 1e-6


def test_stand_labels_present(base):
    plain = st.stand_base(labels=False)
    assert base.volume - plain.volume > 10 * p.label_h


def test_case_centered_on_aa():
    assert abs((p.outer_x0 + p.outer_x1) / 2 - p.aa_cx) < 1e-6
    assert abs((p.outer_y0 + p.outer_y1) / 2 - p.aa_cy) < 1e-6


def test_printed_part_handedness(printable):
    """Pin a known asymmetric feature to its real side. The front shell prints front face down;
    seen from the front (from below the bed, +Y up) the viewer's right is -X. The power notch
    must sit left of the case center, as power_x < aa_cx says in front-view terms."""
    part = printable["front_shell"]
    bb = part.bounding_box()
    cx = (bb.min.X + bb.max.X) / 2
    def at(front_view_x):      # front-view X offset from the case center -> printed X
        return cx - front_view_x
    off = p.power_x - p.aa_cx
    y = bb.max.Y - p.wall / 2
    z = p.front_thickness + 15.0
    probe = lambda x: overlap(part, box(x - 2, x + 2, y - 0.5, y + 0.5, z - 1, z + 1))
    assert probe(at(off)) < 0.01          # notch is here (left seen from the front)
    assert probe(at(-off)) > 1.0          # solid wall at the mirror position
