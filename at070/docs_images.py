"""Render the README images (preview and kickstand installation steps) to docs/images/.

A small orthographic z-buffer renderer over build123d tessellations (numpy + Pillow), with outline
edges from depth and normal breaks. Parts are the real, right-handed geometry (to_world).
"""
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from build123d import Pos, Rot
from at070 import coupons, kickstand as ks, mocks, params as p
from at070.build import to_world
from at070.front_shell import front_shell
from at070.geom import box
from at070.lid import lid

W, H, SS = 1200, 860, 2          # output size, supersampling
COL = {"screen": "#1d2633", "lid": "#c3c7cc", "shell": "#55595f", "flap": "#4c7fb8", "block": "#e08a2e",
       "bar": "#c8423b", "desk": "#efece6"}
INK = (40, 40, 44)


def _rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0


def _mesh(shape, tol):
    verts, tris = shape.tessellate(tol, 0.3)
    v = np.array([(q.X, q.Y, q.Z) for q in verts])
    return v[np.array(tris)]


class Scene:
    """Parts as (shape, color); camera from azimuth/elevation (deg, world Z up)."""

    def __init__(self, az, el, tol=0.05, desk=None, flip=False):
        """flip=True turns everything over (180 deg about X), e.g. to show the lid's inside."""
        self.az, self.el, self.tol, self.desk = math.radians(az), math.radians(el), tol, desk
        self.f = np.array([1, -1, -1.0]) if flip else np.ones(3)
        self.items, self.arrows, self.labels = [], [], []

    def add(self, shape, color):
        self.items.append((_mesh(shape, self.tol) * self.f, _rgb(COL[color])))
        return self

    def arrow(self, a, b):
        self.arrows.append((np.array(a, float) * self.f, np.array(b, float) * self.f))

    def label(self, xyz, text, dx=0, dy=0):
        self.labels.append((np.array(xyz, float) * self.f, text, dx, dy))

    def _camera(self):
        fwd = -np.array([math.cos(self.el) * math.cos(self.az), math.cos(self.el) * math.sin(self.az),
                         math.sin(self.el)])
        right = np.cross(fwd, [0, 0, 1.0])
        right /= np.linalg.norm(right)
        return fwd, right, np.cross(right, fwd)

    def render(self, out, title=None, margin=1.18):
        T = np.vstack([t for t, _ in self.items])
        C = np.vstack([np.repeat(c[None], len(t), 0) for t, c in self.items])
        pid = np.concatenate([np.full(len(t), i) for i, (t, _) in enumerate(self.items)])
        fwd, right, up = self._camera()
        lo, hi = T.reshape(-1, 3).min(0), T.reshape(-1, 3).max(0)
        ctr = (lo + hi) / 2
        pts = T.reshape(-1, 3) - ctr
        for a, b in self.arrows:
            pts = np.vstack([pts, a - ctr, b - ctr])
        span = max(np.ptp(pts @ right) * H / W, np.ptp(pts @ up)) * margin
        ctr = ctr + right * ((pts @ right).max() + (pts @ right).min()) / 2 \
            + up * ((pts @ up).max() + (pts @ up).min()) / 2
        if title:
            span *= 1.08
        w, h = W * SS, H * SS
        scale = h / span

        def proj(q):
            d = np.asarray(q) - ctr
            return w / 2 + (d @ right) * scale, h / 2 - (d @ up) * scale + (0.04 * h if title else 0)

        if self.desk is not None:              # desk plane under everything
            R = np.ptp(T.reshape(-1, 3)[:, :2], axis=0).max() * 1.2
            cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
            d = np.array([[cx - R, cy - R, self.desk], [cx + R, cy - R, self.desk],
                          [cx + R, cy + R, self.desk], [cx - R, cy + R, self.desk]])
            T = np.vstack([T, [[d[0], d[1], d[2]], [d[0], d[2], d[3]]]])
            C = np.vstack([C, [_rgb(COL["desk"])] * 2])
            pid = np.concatenate([pid, [-1, -1]])
        P = T - ctr
        px = w / 2 + (P @ right) * scale
        py = h / 2 - (P @ up) * scale + (0.04 * h if title else 0)
        dep = P @ fwd
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        L = np.array([0.35, -0.55, 0.75])
        L /= np.linalg.norm(L)
        shade = 0.38 + 0.42 * np.abs(n @ L) + 0.20 * np.abs(n @ fwd)
        img = np.ones((h, w, 3))
        zb = np.full((h, w), np.inf)
        tid = np.full((h, w), -1)
        for i in range(len(T)):
            x, y, z = px[i], py[i], dep[i]
            x0, x1 = int(max(0, np.floor(x.min()))), int(min(w - 1, np.ceil(x.max())))
            y0, y1 = int(max(0, np.floor(y.min()))), int(min(h - 1, np.ceil(y.max())))
            if x1 < x0 or y1 < y0:
                continue
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            c = 1 - a - b
            m = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
            zz = a * z[0] + b * z[1] + c * z[2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]
            k = m & (zz < sub)
            sub[k] = zz[k]
            img[y0:y1 + 1, x0:x1 + 1][k] = C[i] * shade[i]
            tid[y0:y1 + 1, x0:x1 + 1][k] = i
        # outlines: part changes, depth jumps, and creases (normal breaks)
        part = np.where(tid >= 0, np.concatenate([pid, [-2]])[tid], -3)
        nrm = np.where(tid[..., None] >= 0, n[np.maximum(tid, 0)], 0)
        edge = np.zeros((h, w), bool)
        thr = 1.5
        for dy, dx in ((0, 1), (1, 0)):
            p2 = np.roll(part, (dy, dx), (0, 1))
            z2 = np.roll(zb, (dy, dx), (0, 1))
            n2 = np.roll(nrm, (dy, dx), (0, 1))
            e = part != p2
            fin = np.isfinite(zb) & np.isfinite(z2)
            with np.errstate(invalid="ignore"):
                e |= fin & (np.abs(zb - z2) > thr)
            e |= fin & ((nrm * n2).sum(-1) < 0.82) & (part == p2) & (part != -2)
            edge |= e
        edge &= ~((part == -2) & (np.roll(part, 1, 0) == -2))   # no lines inside the desk
        img[edge] = img[edge] * 0.25
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        font = ImageFont.load_default(size=17 * SS)
        for a, b in self.arrows:
            (ax, ay), (bx, by) = proj(a), proj(b)
            d.line([(ax, ay), (bx, by)], fill=(200, 30, 30), width=4 * SS)
            ang = math.atan2(by - ay, bx - ax)
            hl = 16 * SS
            d.polygon([(bx, by), (bx - hl * math.cos(ang - 0.45), by - hl * math.sin(ang - 0.45)),
                       (bx - hl * math.cos(ang + 0.45), by - hl * math.sin(ang + 0.45))],
                      fill=(200, 30, 30))
        for q, text, dx, dy in self.labels:
            x, y = proj(q)
            x, y = x + dx * SS, y + dy * SS
            bb = d.textbbox((x, y), text, font=font, anchor="mm")
            d.rectangle([bb[0] - 6 * SS, bb[1] - 4 * SS, bb[2] + 6 * SS, bb[3] + 4 * SS],
                        fill=(255, 255, 255), outline=INK, width=SS)
            d.text((x, y), text, fill=INK, font=font, anchor="mm")
        if title:
            d.text((24 * SS, 20 * SS), title, fill=INK, font=ImageFont.load_default(size=24 * SS))
        im = im.resize((W, H), Image.LANCZOS)
        if out:
            im.save(out)
            print(out)
        return im


# ---------------------------------------------------------------- scenes

def _bc(shape):
    b = shape.bounding_box()
    return np.array([(b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2, (b.min.Z + b.max.Z) / 2])


def preview(out):
    """Case standing in landscape on the main flap (notch nearest 25 deg): front and back views
    side by side."""
    st = min(ks.main_table(), key=lambda t: abs(t["tilt"] - 25))
    shapes = [(front_shell(), "shell"), (lid(), "lid"), (mocks.panel(), "screen")]
    for name, s in ks.all_parts(main_opening=st["opening"]).items():
        shapes.append((s, "flap" if name.endswith("flap") else "bar" if "bar" in name else "block"))
    R = Rot(X=90 + st["tilt"])
    posed = [(R * to_world(s), c) for s, c in shapes]
    zmin = min(s.bounding_box().min.Z for s, _ in posed)
    views = []
    for az, title in ((55, f"Front, landscape at {st['tilt']:.0f} deg"),
                      (-120, "Back: kickstand open")):
        sc = Scene(az=az, el=20, tol=0.15, desk=0.0)
        for s, c in posed:
            sc.add(Pos(0, 0, -zmin) * s, c)
        views.append(sc.render(None, title))
    im = Image.new("RGB", (2 * W, H), "white")
    for i, v in enumerate(views):
        im.paste(v, (i * W, 0))
    im.resize((W * 3 // 2, H * 3 // 4), Image.LANCZOS).save(out)
    print(out)


def _coupon(opening=0.0):
    lid_piece = coupons.coupon_hinge_lid()
    plain, spring = coupons.coupon_hinge_blocks()
    bars = coupons.coupon_hinge_bars()
    return lid_piece, coupons.coupon_hinge_flap(opening), plain, spring, bars


def step1(out):
    """Pins into the knuckle ends: blocks pulled out along the hinge axis."""
    _, f, plain, spring, _ = _coupon()
    gap = 12.0
    plain_o, spring_o = Pos(-gap, 0, 0) * plain, Pos(gap, 0, 0) * spring
    sc = Scene(az=-65, el=30)
    sc.add(to_world(f), "flap").add(to_world(plain_o), "block").add(to_world(spring_o), "block")
    za = p.z_lid_top + p.ks_axis_z
    xp, xs = ks.block_x0s(p.coupon_hinge_w)
    m = np.array([-1, 1, 1])          # to_world mirrors X
    a0 = np.array([xp - gap + p.ks_block_w + p.ks_pin_len + 1, 0, za + 9])
    sc.arrow(a0 * m, (a0 + [gap - 2, 0, 0]) * m)
    b0 = np.array([xs + gap - p.ks_leaf_len - 1, 0, za + 9])
    sc.arrow(b0 * m, (b0 - [gap - 2, 0, 0]) * m)
    sc.label(_bc(to_world(plain_o)) + [0, 0, 9], "plain block", dy=-40)
    sc.label(_bc(to_world(spring_o)) + [0, 0, 9], "spring block (cam end)", dy=-40)
    sc.render(out, "1. Push both blocks' pins into the knuckle ends")


def step2(out):
    """Flap with blocks lowered onto the lid: posts into the slots."""
    lid_piece, f, plain, spring, _ = _coupon()
    lift = Pos(0, 0, 16)
    sc = Scene(az=-65, el=35)
    sc.add(to_world(lid_piece), "lid")
    sc.add(to_world(lift * f), "flap").add(to_world(lift * plain), "block").add(to_world(lift * spring), "block")
    for blk in (plain, spring):
        c = _bc(to_world(blk))
        sc.arrow(c + [0, -12, 14], c + [0, -12, 4])
    sc.label(_bc(to_world(lid_piece)) + [0, -17, 0], "posts drop into the lid slots", dy=60)
    sc.render(out, "2. Set it on the lid back, posts into the slots")


def _under(bar_shift):
    lid_piece, f, plain, spring, bars = _coupon()
    sc = Scene(az=-30, el=32, flip=True)
    sc.add(to_world(lid_piece), "lid").add(to_world(f), "flap")
    sc.add(to_world(plain), "block").add(to_world(spring), "block")
    for b in bars:
        sc.add(to_world(Pos(0, -bar_shift, 0) * b), "bar")
    return sc, bars


def step3(out):
    """Lid turned over: bars about to slide in through both posts."""
    shift = 16.0
    sc, bars = _under(shift)
    z_arrow = p.z_lid_top - 10.5          # below the bars (above them once the lid is turned over)
    for b in bars:
        c = _bc(to_world(b))
        sc.arrow([c[0], ks.bar_ends()[0] - shift - 4, z_arrow], [c[0], ks.bar_ends()[0] - 1, z_arrow])
    c = _bc(to_world(bars[0]))
    sc.label([c[0], ks.bar_ends()[1] - shift, c[2]], "thin end first", dy=-45)
    sc.render(out, "3. Turn the lid over, slide a wedge bar through each block's posts")


def step4(out):
    sc, bars = _under(0.0)
    sc.render(out, "4. Push each bar until tight; it clamps the block flat (pull the tab to remove)")


def section(out):
    """Cut through the middle of the spring block, seen along the hinge axis."""
    lid_piece, f, plain, spring, bars = _coupon(52.0)
    xs = ks.block_x0s(p.coupon_hinge_w)[1] + p.ks_block_w / 2
    cut = box(xs, 200, -100, 100, -100, 100)
    sc = Scene(az=180, el=0)
    sc.add(to_world(lid_piece - cut), "lid").add(to_world(f - cut), "flap")
    sc.add(to_world(spring - cut), "block").add(to_world(bars[1] - cut), "bar")
    z0, zt = p.z_rim, p.z_lid_top
    yh = ks.bar_ends()[0]
    sc.label((-xs, yh - 1, z0 - 7), "pull tab", dx=80)
    sc.label((-xs, 0, z0 - 2), "wedge bar", dy=45)
    for y in (-6.8, 6.8):
        sc.label((-xs, y, zt + ks.post_tip_z(1 if y > 0 else -1)), "post", dy=28)
    sc.label((-xs, 15, zt - 1.2), "lid", dy=-40)
    sc.label((-xs, -8, zt + 10), "flap", dx=60)
    sc.render(out, "How it holds: section through a hinge block")


def overview(out):
    """Whole lid from the inside with all four bars in place."""
    sc = Scene(az=-90, el=-62, tol=0.15)
    sc.add(to_world(lid()), "lid")
    for name, s in ks.all_parts().items():
        sc.add(to_world(s), "flap" if name.endswith("flap") else "bar" if "bar" in name else "block")
    for name, s in ks.all_parts().items():
        if "bar" in name:
            main = name.startswith("main")
            sc.label(_bc(to_world(s)), "main flap bar" if main else "prop bar",
                     dx=0 if main else 110, dy=-40 if main else 0)
    sc.render(out, "Inside of the lid: the four bars (main flap and prop)")


def _kind(name):
    return "flap" if name.endswith("flap") else "bar" if "bar" in name else "block"


def portrait(out):
    """Case standing in portrait on its +X short edge, leaning back on the prop: front and back."""
    st = ks.prop_state()
    shapes = [(front_shell(), "shell"), (lid(), "lid"), (mocks.panel(), "screen")]
    shapes += [(s, _kind(n)) for n, s in ks.all_parts(prop_opening=max(p.ks_prop_notches)).items()]
    R = Rot(X=90 + st["tilt"]) * Rot(Z=90)      # world -X (the model's +X edge) down
    posed = [(R * to_world(s), c) for s, c in shapes]
    zmin = min(s.bounding_box().min.Z for s, _ in posed)
    views = []
    for az, title in ((60, f"Portrait on the prop, {st['tilt']:.1f} deg"), (-115, "Back: prop open")):
        sc = Scene(az=az, el=20, tol=0.15, desk=0.0)
        for s, c in posed:
            sc.add(Pos(0, 0, -zmin) * s, c)
        views.append(sc.render(None, title))
    im = Image.new("RGB", (2 * W, H), "white")
    for i, v in enumerate(views):
        im.paste(v, (i * W, 0))
    im.resize((W * 3 // 2, H * 3 // 4), Image.LANCZOS).save(out)
    print(out)


def exploded(out):
    """Every printed part pulled apart along the case depth, front shell first."""
    gap = {"shell": 0, "screen": 30, "bar": 58, "lid": 100, "block": 140, "flap": 170}
    shapes = [(front_shell(), "shell"), (mocks.panel(), "screen"), (lid(), "lid")]
    shapes += [(s, _kind(n)) for n, s in ks.all_parts().items()]
    sc = Scene(az=-125, el=28, tol=0.15)
    for s, c in shapes:
        sc.add(Pos(0, 0, gap[c]) * to_world(s), c)
    sc.render(out, "Exploded: front shell, panel, wedge bars, lid, hinge blocks, flap and prop")


SCENES = {"preview": preview, "portrait": portrait, "exploded": exploded, "install_1_pins": step1, "install_2_posts": step2,
          "install_3_bars": step3, "install_4_seated": step4, "clamp_section": section,
          "install_overview": overview}


def main(out_dir="docs/images", *names):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in names or SCENES:
        SCENES[name](str(out / f"{name}.png"))


if __name__ == "__main__":
    main(*sys.argv[1:])
