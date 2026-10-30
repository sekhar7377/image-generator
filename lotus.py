"""Render a lotus flower floating on a calm lake at dawn (procedural, PIL + numpy)."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1600, 1000
SS = 2  # supersampling factor for smooth edges
HORIZON = 0.42
random.seed(7)
np.random.seed(7)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def vertical_gradient(w, h, stops):
    ys = np.linspace(0, 1, h)
    img = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        col = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
        img[:, :, c] = col[:, None]
    return img


def sky_and_lake(w, h):
    hy = int(h * HORIZON)
    sky = vertical_gradient(w, hy, [
        (0.0, (120, 150, 200)), (0.55, (240, 190, 200)), (1.0, (255, 220, 190))])
    # soft sun glow
    yy, xx = np.mgrid[0:hy, 0:w]
    sx, sy = w * 0.68, hy * 0.92
    d = np.sqrt((xx - sx) ** 2 + ((yy - sy) * 1.3) ** 2)
    glow = np.exp(-(d / (w * 0.12)) ** 2)[..., None]
    sky = sky * (1 - glow * 0.6) + np.array([255, 245, 225]) * glow * 0.6

    lake = vertical_gradient(w, h - hy, [
        (0.0, (200, 175, 190)), (0.15, (110, 140, 170)), (1.0, (25, 55, 80))])
    # mirrored sun glow on water, stretched vertically
    yy, xx = np.mgrid[0:h - hy, 0:w]
    d = np.sqrt(((xx - sx) * 1.6) ** 2 + (yy * 0.35) ** 2)
    g2 = np.exp(-(d / (w * 0.12)) ** 2)[..., None] * 0.5
    lake = lake * (1 - g2) + np.array([255, 235, 215]) * g2
    return np.concatenate([sky, lake], axis=0), hy


def hills(draw, w, hy):
    for layer, (col, amp, base) in enumerate([
            ((150, 140, 175), 0.09, 0.03), ((105, 110, 140), 0.06, 0.0)]):
        pts = [(0, hy)]
        phase = random.random() * 10
        for x in range(0, w + 10, 10):
            y = hy - (base + amp * (0.6 + 0.4 * math.sin(x / w * 5 + phase)
                                   * math.cos(x / w * 2.3 + layer))) * w * 0.35
            pts.append((x, y))
        pts.append((w, hy))
        draw.polygon(pts, fill=col)


def ripples(draw, w, h, hy):
    for _ in range(420):
        y = random.uniform(hy + 4, h)
        depth = (y - hy) / (h - hy)
        length = random.uniform(30, 200) * (0.4 + depth)
        x = random.uniform(-50, w)
        thick = max(1, int(1 + depth * 3 * SS / 2))
        light = random.random() < 0.55
        col = (235, 225, 235, int(40 + 50 * depth)) if light else (20, 40, 60, int(50 + 60 * depth))
        draw.line([(x, y), (x + length, y)], fill=col, width=thick)


def lily_pad(draw, cx, cy, r, tilt=0.38, notch=None):
    notch = random.uniform(0, 360) if notch is None else notch
    rx, ry = r, r * tilt
    pts = []
    for a in range(0, 360, 3):
        diff = (a - notch + 360) % 360
        if diff < 18 or diff > 342:
            continue
        t = math.radians(a)
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    pts.append((cx, cy))
    # shadow
    draw.polygon([(x + 4 * SS, y + 5 * SS) for x, y in pts], fill=(10, 30, 35, 90))
    draw.polygon(pts, fill=(45, 110, 60, 255))
    inner = [(cx + (x - cx) * 0.88, cy + (y - cy) * 0.88) for x, y in pts]
    draw.polygon(inner, fill=(70, 140, 70, 255))
    inner2 = [(cx + (x - cx) * 0.55, cy + (y - cy) * 0.55 - ry * 0.05) for x, y in pts]
    draw.polygon(inner2, fill=(90, 160, 85, 255))
    for a in range(0, 360, 30):  # veins
        diff = (a - notch + 360) % 360
        if diff < 20 or diff > 340:
            continue
        t = math.radians(a)
        draw.line([(cx, cy), (cx + rx * 0.85 * math.cos(t), cy + ry * 0.85 * math.sin(t))],
                  fill=(55, 120, 60, 180), width=SS)


def petal_poly(bx, by, length, width, angle_deg, squash=1.0, n=40):
    """Pointed teardrop petal from base (bx,by) toward angle (0 = up)."""
    a = math.radians(angle_deg)
    ux, uy = math.sin(a), -math.cos(a)
    px, py = -uy, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        wdt = width * (math.sin(math.pi * t ** 0.85) ** 0.9) * (1 - 0.25 * t)
        along = length * t
        x0, y0 = bx + ux * along, by + uy * along * squash
        left.append((x0 + px * wdt, y0 + py * wdt * squash))
        right.append((x0 - px * wdt, y0 - py * wdt * squash))
    return left + right[::-1]


def shrink(poly, cx, cy, f):
    return [(cx + (x - cx) * f, cy + (y - cy) * f) for x, y in poly]


def draw_petal(draw, bx, by, length, width, angle, squash=1.0, dark=False):
    poly = petal_poly(bx, by, length, width, angle, squash)
    tip = (235, 95, 150) if not dark else (205, 70, 125)
    mid = (250, 170, 200) if not dark else (230, 140, 175)
    base = (255, 245, 240)
    draw.polygon(poly, fill=tip + (255,), outline=(190, 60, 115, 255))
    # layered gradient: base-anchored scaled copies become lighter toward the base
    steps = 9
    for i in range(1, steps + 1):
        f = 1 - i / (steps + 1)
        col = lerp(tip, mid, i / steps) if i < steps * 0.6 else lerp(mid, base, (i - steps * 0.6) / (steps * 0.4))
        draw.polygon(shrink(poly, bx, by, f), fill=col + (255,))
    # central vein
    a = math.radians(angle)
    draw.line([(bx, by), (bx + math.sin(a) * length * 0.8, by - math.cos(a) * length * 0.8 * squash)],
              fill=(230, 120, 165, 140), width=SS)


def lotus(draw, cx, cy, s):
    # back row: wide, low petals
    for ang in (-78, -55, 55, 78, -100, 100):
        draw_petal(draw, cx, cy, 170 * s, 48 * s, ang, squash=0.75, dark=True)
    # middle row
    for ang in (-40, -20, 20, 40):
        draw_petal(draw, cx, cy, 200 * s, 52 * s, ang)
    # seed pod hint
    draw.ellipse([cx - 30 * s, cy - 120 * s, cx + 30 * s, cy - 95 * s], fill=(235, 205, 90, 255))
    # inner upright petals
    for ang in (-10, 10, 0):
        draw_petal(draw, cx, cy, 195 * s, 44 * s, ang)
    # front petals overlapping the base
    for ang in (-62, 62, -32, 32):
        draw_petal(draw, cx, cy + 6 * s, 150 * s, 50 * s, ang, squash=0.85)


def main():
    w, h = W * SS, H * SS
    bg, hy = sky_and_lake(w, h)
    img = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    hills(d, w, hy)

    # hill reflection (flipped, softened)
    top = img.crop((0, int(hy * 0.6), w, hy)).transpose(Image.FLIP_TOP_BOTTOM)
    top = top.filter(ImageFilter.GaussianBlur(6 * SS))
    fade = np.linspace(110, 0, top.height)[:, None].repeat(w, axis=1).astype(np.uint8)
    top.putalpha(Image.fromarray(fade))
    img.alpha_composite(top, (0, hy))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ripples(ImageDraw.Draw(overlay), w, h, hy)
    img.alpha_composite(overlay)

    # pads: background small, foreground big
    pads = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pads)
    pad_specs = [(0.12, 0.58, 55), (0.30, 0.55, 40), (0.85, 0.57, 50), (0.93, 0.66, 75),
                 (0.07, 0.80, 130), (0.25, 0.92, 170), (0.78, 0.86, 150), (0.66, 0.97, 120),
                 (0.40, 0.70, 70), (0.60, 0.66, 60)]
    for fx, fy, r in pad_specs:
        lily_pad(pd, fx * w, fy * h, r * SS)
    img.alpha_composite(pads)

    # main lotus, with its reflection
    cx, cy, s = w * 0.5, h * 0.78, 1.25 * SS
    flower = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    lily_pad(ImageDraw.Draw(flower), cx + 20 * SS, cy + 15 * SS, 230 * SS, notch=300)
    fl = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    lotus(ImageDraw.Draw(fl), cx, cy, s)

    refl = fl.crop((0, 0, w, int(cy))).transpose(Image.FLIP_TOP_BOTTOM)
    refl = refl.filter(ImageFilter.GaussianBlur(5 * SS))
    fade = np.linspace(0.4, 0.0, refl.height)[:, None]
    r_alpha = (np.asarray(refl.getchannel("A"), dtype=np.float32) * fade).astype(np.uint8)
    refl.putalpha(Image.fromarray(r_alpha))
    img.alpha_composite(refl, (0, int(cy)))
    img.alpha_composite(flower)

    # soft glow behind the flower
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - 260 * s, cy - 300 * s, cx + 260 * s, cy + 40 * s],
                                 fill=(255, 210, 230, 70))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60 * SS)))
    img.alpha_composite(fl)

    # smaller buds/flowers in the distance
    for fx, fy, sc in [(0.85, 0.62, 0.35), (0.18, 0.70, 0.45)]:
        small = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        lotus(ImageDraw.Draw(small), fx * w, fy * h, sc * SS)
        img.alpha_composite(small)

    out = img.convert("RGB").resize((W, H), Image.LANCZOS)
    out.save("lotus_lake.png", optimize=True)
    print("saved lotus_lake.png")


if __name__ == "__main__":
    main()
