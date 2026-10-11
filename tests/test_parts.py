import pytest
from build123d import Axis
from at070 import coupons, mocks, params as p
from at070.build import printable_parts
from at070.front_shell import front_shell
from at070.geom import box
from at070.lid import clip_strain, lid, press_ribs
from at070.stand import base_y_range, com_y, stand


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


@pytest.mark.parametrize("name", ["front_shell", "lid", "stand", "coupon_fit_frame",
                                  "coupon_top_edge_front", "coupon_top_edge_lid"])
def test_single_valid_solid_fits_and_on_bed(printable, name):
    part = printable[name]
    assert part.is_valid
    assert len(part.solids()) == 1
    bb = part.bounding_box()
    assert abs(bb.min.Z) < 1e-6
    assert bb.size.X <= 250 and bb.size.Y <= 250 and bb.size.Z <= 250


def test_unoriented_parts_single_solid(shell, lid_part):
    for s in (shell, lid_part, stand()):
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


def test_stand_dimensions():
    assert p.groove_w >= p.case_depth + 0.6
    assert p.stand_w < min(p.outer_w, p.outer_h)


@pytest.mark.parametrize("case_h", [min(p.outer_w, p.outer_h), max(p.outer_w, p.outer_h)])
def test_stand_center_of_mass(case_h):
    y0, y1 = base_y_range()
    y = com_y(case_h)
    assert y - y0 >= p.com_min_edge
    assert y1 - y >= p.com_min_edge


def test_stand_bbox():
    bb = stand().bounding_box()
    assert abs(bb.min.Z) < 1e-6 and abs(bb.size.Z - p.rest_top_z) < 1e-6


def test_case_centered_on_aa():
    assert abs((p.outer_x0 + p.outer_x1) / 2 - p.aa_cx) < 1e-6
    assert abs((p.outer_y0 + p.outer_y1) / 2 - p.aa_cy) < 1e-6
