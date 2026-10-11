"""Export all printable parts (print orientation, on Z = 0) and an assembly STEP to out/."""
import sys
from pathlib import Path
from build123d import Compound, Mesher, Plane, Pos, Rot, export_step, export_stl
from at070 import coupons, mocks
from at070.front_shell import front_shell
from at070.lid import lid
from at070.stand import stand


def to_world(shape):
    """Model frame -> real part. The model's +X is "right seen from the front" with +Z toward
    the back, which is left-handed; mirroring X gives the right-handed part that prints."""
    return shape.mirror(Plane.YZ)


def _sit(shape):
    z = shape.bounding_box().min.Z
    return Pos(0, 0, -z) * shape


def _on_bed(shape):
    """Real part, front face down, on Z = 0."""
    return _sit(to_world(shape))


def flip(shape):
    """Real part rotated 180 deg about X (back face down), on Z = 0."""
    return _sit(Rot(X=180) * to_world(shape))


def printable_parts():
    """Dict name -> print-oriented solid sitting on Z = 0."""
    return {
        "front_shell": _on_bed(front_shell()),
        "lid": flip(lid()),
        "stand": _on_bed(stand()),
        "coupon_fit_frame": _on_bed(coupons.coupon_fit_frame()),
        "coupon_top_edge_front": _on_bed(coupons.coupon_top_edge_front()),
        "coupon_top_edge_lid": flip(coupons.coupon_top_edge_lid()),
    }


def assembly():
    parts = [("front_shell", front_shell()), ("lid", lid()), ("panel", mocks.panel()),
             ("board_keepout", mocks.board_keepout()), ("hdmi_plug", mocks.hdmi_plug()),
             ("power_cable", mocks.power_cable())]
    parts = [(name, to_world(s)) for name, s in parts]
    for name, s in parts:
        s.label = name
    return Compound(children=[s for _, s in parts], label="assembly")


def main(out_dir="out"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, part in printable_parts().items():
        export_step(part, str(out / f"{name}.step"))
        export_stl(part, str(out / f"{name}.stl"))
        m = Mesher()
        m.add_shape(part, linear_deflection=0.01, angular_deflection=0.1)
        m.write(str(out / f"{name}.3mf"))
        bb = part.bounding_box()
        print(f"{name}: bbox {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"volume {part.volume / 1000:.2f} cm3")
    export_step(assembly(), str(out / "assembly.step"))
    print("assembly.step written")


if __name__ == "__main__":
    main(*sys.argv[1:2])
