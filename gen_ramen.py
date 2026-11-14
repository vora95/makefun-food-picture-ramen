"""Draw a steaming bowl of ramen, procedurally, with PIL + numpy.

This is the generator that drew the entry's shipped picture (entry.png):
an overhead flat-lay of a bowl of ramen. No photo, no external assets, no
paid service: every pixel is computed here.
Overhead flat-lay: ceramic bowl, golden broth, noodle swirl lifted by
chopsticks, ajitama egg, chashu, nori, green onion, narutomaki, steam.
Renders at 2x (2048) and downsamples to 1024 for smooth edges.
Output: entry-ramen-final.jpg (the shipped image, 1024x1024).
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2
W = H = 1024 * SS
OUT = 1024
rng = random.Random(20261115)


def radial_bg(size, center, inner, mid, outer):
    s = 256
    yy, xx = np.mgrid[0:s, 0:s]
    cx, cy = center[0] / size * s, center[1] / size * s
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (s * 0.62)
    d = np.clip(d, 0, 1)
    inner = np.array(inner, float)
    mid = np.array(mid, float)
    outer = np.array(outer, float)
    t1 = np.clip(d / 0.55, 0, 1)[..., None]
    t2 = np.clip((d - 0.55) / 0.45, 0, 1)[..., None]
    col = inner * (1 - t1) + mid * t1
    col = col * (1 - t2) + outer * t2
    return Image.fromarray(col.astype(np.uint8), "RGB").resize((size, size), Image.BICUBIC)


def vgrad(w, h, top, bottom):
    s = 256
    t = np.linspace(0, 1, s)[:, None, None]
    col = np.array(top, float) * (1 - t) + np.array(bottom, float) * t
    col = np.repeat(col, 4, axis=1)
    return Image.fromarray(col.astype(np.uint8), "RGB").resize((w, h), Image.BICUBIC)


def soft_layer(size, draw_fn, blur):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d)
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return layer


def radial_patch(w, h, cx, cy, radius, inner, outer):
    s = 128
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt(((xx - cx / w * s) ** 2 + (yy - cy / h * s) ** 2)) / (radius / w * s)
    d = np.clip(d, 0, 1)[..., None]
    col = np.array(inner, float) * (1 - d) + np.array(outer, float) * d
    return Image.fromarray(col.astype(np.uint8), "RGB").resize((w, h), Image.BICUBIC)


def ring(d, cx, cy, r, width, fill):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fill, width=width)


def contact_shadow(img, x, y, rx, ry, alpha=90, blur=18):
    """Soft dark ellipse under a topping, so it sits IN the broth, not on it."""
    img.alpha_composite(soft_layer(img.size, lambda d: d.ellipse(
        [x - rx, y - ry, x + rx, y + ry], fill=(0, 0, 0, alpha)), blur))


def draw_ramen():
    # ---- warm dark wooden table --------------------------------------------
    img = radial_bg(W, (W // 2, int(H * 0.42)), (88, 54, 30), (48, 28, 16), (18, 11, 7))
    img = img.convert("RGBA")
    # wood planks: faint horizontal bands + grain
    planks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(planks)
    for y in range(0, H, 340):
        pd.line([(0, y), (W, y)], fill=(0, 0, 0, 32), width=3)
        for _ in range(8):
            gx = rng.randint(0, W)
            gy = y + rng.randint(20, 320)
            gl = rng.randint(120, 420)
            pd.line([(gx, gy), (gx + gl, gy + rng.randint(-6, 6))],
                    fill=(30, 16, 8, 40), width=3)
    img.alpha_composite(planks)
    # warm spotlight
    img.alpha_composite(soft_layer((W, H), lambda d: d.ellipse(
        [W // 2 - 700, 240, W // 2 + 700, 1640], fill=(255, 170, 90, 55)), 200))

    cx, cy = W // 2, 1180          # bowl centre (1024 coords: 512, 590)
    R = 700                        # outer bowl radius

    # ---- bowl shadow on the table -------------------------------------------
    img.alpha_composite(soft_layer((W, H), lambda d: d.ellipse(
        [cx - R - 40, cy - R + 260, cx + R + 90, cy + R + 120],
        fill=(0, 0, 0, 120)), 70))

    # ---- bowl: dark ceramic exterior, cream rim ------------------------------
    bowl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bowl)
    # exterior: deep indigo-black with radial light
    ext = radial_patch(2 * R + 40, 2 * R + 40, R - 160, R - 220, R + 200,
                       (52, 58, 92), (16, 18, 34))
    emask = Image.new("L", (W, H), 0)
    emd = ImageDraw.Draw(emask)
    emd.ellipse([cx - R, cy - R, cx + R, cy + R], fill=255)
    bowl.paste(ext, (cx - R - 20, cy - R - 20),
               emask.crop((cx - R - 20, cy - R - 20, cx + R + 20, cy + R + 20)))
    bd.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(8, 9, 18, 255), width=6)
    # cream rim ring
    ring(bd, cx, cy, R - 55, 34, (238, 226, 200, 255))
    ring(bd, cx, cy, R - 38, 6, (180, 164, 132, 255))
    ring(bd, cx, cy, R - 74, 6, (180, 164, 132, 255))
    # rim light: soft arc top-left
    bd.arc([cx - R, cy - R, cx + R, cy + R], 140, 320,
           fill=(255, 250, 235, 220), width=10)
    img.alpha_composite(bowl)

    # ---- broth: rich golden-brown, glossy ------------------------------------
    broth = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    brd = ImageDraw.Draw(broth)
    br = R - 90
    bg = radial_patch(2 * br, 2 * br, br - 120, br - 140, br + 60,
                      (232, 158, 62), (128, 66, 18))
    bmask = Image.new("L", (W, H), 0)
    bmd = ImageDraw.Draw(bmask)
    bmd.ellipse([cx - br, cy - br, cx + br, cy + br], fill=255)
    broth.paste(bg, (cx - br, cy - br), bmask.crop((cx - br, cy - br, cx + br, cy + br)))
    # chili-oil swirls: red-orange translucent arcs on the broth
    for _ in range(14):
        a0 = rng.uniform(0, 360)
        a1 = a0 + rng.uniform(50, 150)
        rr = rng.uniform(br * 0.45, br * 0.95)
        brd.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a1,
                fill=(206, 66, 22, 190), width=rng.randint(14, 30))
    # oil droplets: glossy amber dots
    for _ in range(26):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, br * 0.9)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        r = rng.randint(6, 18)
        brd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 176, 66, 170))
        brd.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.1, y + r * 0.1],
                    fill=(255, 224, 150, 200))
    img.alpha_composite(broth)

    # ---- noodles in the broth: dense, wavy, tangled --------------------------------
    noodles = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noodles)
    for _ in range(230):
        a0 = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(br * 0.05, br * 0.85)
        nx, ny = cx + rr * math.cos(a0), cy + rr * math.sin(a0)
        sweep = rng.uniform(40, 140)
        r2 = rng.uniform(26, 80)
        # elliptical arcs: wider than tall, so they read as noodle curls, not rings
        w2 = r2 * rng.uniform(1.2, 1.9)
        col = rng.choice([(240, 214, 130, 240), (232, 200, 108, 240),
                          (246, 226, 150, 240), (226, 190, 96, 240)])
        nd.arc([nx - w2, ny - r2, nx + w2, ny + r2],
               rng.uniform(0, 360), rng.uniform(0, 360) + sweep,
               fill=col, width=rng.randint(8, 14))
    img.alpha_composite(noodles)

    # ---- chashu slices (left) -------------------------------------------------
    for i, (ox, oy, rr) in enumerate([(-330, -120, 150), (-210, 40, 145), (-330, 180, 140)]):
        contact_shadow(img, cx + ox + 14, cy + oy + 18, rr + 6, rr * 0.55)
        ch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        chd = ImageDraw.Draw(ch)
        x, y = cx + ox, cy + oy
        chd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(196, 110, 88, 255))
        chd.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(120, 52, 40, 255), width=5)
        chd.ellipse([x - rr * 0.62, y - rr * 0.62, x + rr * 0.62, y + rr * 0.62],
                    fill=(232, 176, 150, 255))
        chd.ellipse([x - rr * 0.34, y - rr * 0.34, x + rr * 0.34, y + rr * 0.34],
                    fill=(198, 112, 90, 255))
        # seared edge + gloss
        chd.arc([x - rr, y - rr, x + rr, y + rr], 200, 330, fill=(90, 36, 26, 220), width=8)
        chd.ellipse([x - rr * 0.5, y - rr * 0.7, x - rr * 0.1, y - rr * 0.3],
                    fill=(255, 220, 200, 130))
        img.alpha_composite(ch)

    # ---- ajitama egg halves (right) --------------------------------------------
    for ox, oy in [(300, -190), (330, 90)]:
        contact_shadow(img, cx + ox + 12, cy + oy + 16, 140, 66)
        eg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ed = ImageDraw.Draw(eg)
        x, y = cx + ox, cy + oy
        ed.ellipse([x - 130, y - 105, x + 130, y + 105], fill=(250, 244, 228, 255))
        ed.ellipse([x - 130, y - 105, x + 130, y + 105], outline=(214, 198, 168, 255), width=4)
        yolk = radial_patch(190, 190, 85, 80, 130, (255, 176, 66), (224, 110, 18))
        ymask = Image.new("L", (W, H), 0)
        ymd = ImageDraw.Draw(ymask)
        ymd.ellipse([x - 88, y - 88, x + 88, y + 88], fill=255)
        eg.paste(yolk, (x - 95, y - 95), ymask.crop((x - 95, y - 95, x + 95, y + 95)))
        ed.ellipse([x - 88, y - 88, x + 88, y + 88], outline=(190, 92, 12, 255), width=4)
        ed.ellipse([x - 52, y - 58, x - 8, y - 18], fill=(255, 224, 150, 200))
        img.alpha_composite(eg)

    # ---- narutomaki (top) --------------------------------------------------------
    contact_shadow(img, cx + 72, cy - 316, 105, 60)
    nar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nard = ImageDraw.Draw(nar)
    x, y = cx + 60, cy - 330
    nard.ellipse([x - 95, y - 95, x + 95, y + 95], fill=(250, 246, 238, 255))
    nard.ellipse([x - 95, y - 95, x + 95, y + 95], outline=(220, 208, 188, 255), width=4)
    # pink spiral
    for t in range(0, 720, 6):
        a = math.radians(t)
        rr = 78 * t / 720
        px, py = x + rr * math.cos(a), y + rr * math.sin(a)
        nard.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(240, 120, 150, 255))
    img.alpha_composite(nar)

    # ---- nori sheet standing at the back ------------------------------------------
    # Tilted, rising above the bowl rim, its base sunk into the broth.
    contact_shadow(img, cx - 330, cy - 290, 150, 42, alpha=110)
    nori = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nod = ImageDraw.Draw(nori)
    nx0, ny0, nx1, ny1 = cx - 460, cy - 800, cx - 200, cy - 300
    ng = vgrad(nx1 - (nx0 - 30), ny1 - ny0, (36, 52, 34), (12, 20, 12))
    nmask = Image.new("L", (W, H), 0)
    nmd = ImageDraw.Draw(nmask)
    nmd.polygon([(nx0, ny1), (nx1, ny1), (nx1 - 30, ny0), (nx0 - 30, ny0)], fill=255)
    nori.paste(ng, (nx0 - 30, ny0), nmask.crop((nx0 - 30, ny0, nx1, ny1)))
    nod.polygon([(nx0, ny1), (nx1, ny1), (nx1 - 30, ny0), (nx0 - 30, ny0)],
                outline=(64, 92, 58, 255), width=4)
    nod.line([(nx0 + 40, ny1 - 40), (nx0 + 10, ny0 + 40)],
             fill=(96, 128, 84, 170), width=6)
    img.alpha_composite(nori)

    # ---- green onion rings scattered ------------------------------------------------
    onion = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(onion)
    for _ in range(46):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(br * 0.15, br * 0.92)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        r = rng.randint(10, 20)
        od.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8],
                   fill=(96, 180, 70, 255))
        od.ellipse([x - r * 0.45, y - r * 0.36, x + r * 0.45, y + r * 0.36],
                   fill=(214, 240, 150, 255))
    img.alpha_composite(onion)

    # ---- sesame + chili flakes -------------------------------------------------------
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(top)
    for _ in range(40):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, br * 0.9)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        td.ellipse([x - 7, y - 4, x + 7, y + 4], fill=(255, 240, 200, 230))
    for _ in range(24):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0, br * 0.85)
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        td.ellipse([x - 8, y - 5, x + 8, y + 5], fill=(196, 48, 24, 230))
    img.alpha_composite(top)

    # ---- chopsticks lifting a noodle swirl (top-right) --------------------------------
    # noodle bundle first (behind the sticks), then the sticks on top
    lift = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lift)
    bx, by = cx + 390, cy - 480   # bundle centre, above the broth
    for _ in range(34):
        a0 = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(10, 120)
        nx, ny = bx + rr * math.cos(a0) * 1.4, by + rr * math.sin(a0) * 0.7
        r2 = rng.uniform(20, 60)
        col = rng.choice([(240, 214, 130, 240), (232, 200, 108, 240),
                          (246, 226, 150, 240)])
        ld.arc([nx - r2, ny - r2, nx + r2, ny + r2],
               rng.uniform(0, 360), rng.uniform(0, 360) + rng.uniform(50, 130),
               fill=col, width=rng.randint(8, 13))
    # dangling strands from the bundle down into the broth
    for _ in range(10):
        x0 = bx + rng.uniform(-110, 110)
        pts = [(x0, by + 60)]
        for k in range(1, 5):
            pts.append((x0 + rng.uniform(-26, 26) + k * 14,
                        by + 60 + k * 78))
        ld.line(pts, fill=(238, 210, 124, 235), width=11, joint="curve")
    img.alpha_composite(lift)

    sticks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    std = ImageDraw.Draw(sticks)
    # two wooden chopsticks, diagonal from top-right down to the bundle
    for off in (0, 46):
        x0, y0 = cx + 700 + off, cy - 780 + off // 2
        x1, y1 = bx + 60 + off, by - 30 + off // 3
        std.line([(x0, y0), (x1, y1)], fill=(150, 96, 52, 255), width=26)
        std.line([(x0, y0 - 8), (x1, y1 - 8)], fill=(196, 138, 82, 255), width=8)
    img.alpha_composite(sticks)

    # ---- steam: soft white curls above the bowl ---------------------------------------
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stmd = ImageDraw.Draw(steam)
    for sx, sw in [(cx - 260, 90), (cx - 40, 110), (cx + 220, 85)]:
        pts = []
        for k in range(21):
            t = k / 20
            pts.append((sx + sw * math.sin(t * math.pi * 2.2), cy - R - 60 - t * 520))
        stmd.line(pts, fill=(255, 255, 255, 175), width=52, joint="curve")
    steam = steam.filter(ImageFilter.GaussianBlur(36))
    img.alpha_composite(steam)

    # ---- broth gloss: big soft highlight top-left ---------------------------------------
    img.alpha_composite(soft_layer((W, H), lambda d: d.ellipse(
        [cx - 480, cy - 560, cx - 60, cy - 220], fill=(255, 220, 150, 70)), 60))

    # ---- grade + downsample --------------------------------------------------------------
    img = img.convert("RGB").resize((OUT, OUT), Image.LANCZOS)
    arr = np.asarray(img).astype(np.float32)
    noise = np.random.default_rng(11).normal(0, 3.0, arr.shape[:2])
    arr += noise[..., None]
    yy, xx = np.mgrid[0:OUT, 0:OUT]
    d = np.sqrt(((xx - OUT / 2) / (OUT * 0.72)) ** 2 + ((yy - OUT / 2) / (OUT * 0.72)) ** 2)
    vig = np.clip(1 - 0.22 * np.clip(d - 0.55, 0, 1) ** 2, 0, 1)
    arr *= vig[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


if __name__ == "__main__":
    from PIL import ImageEnhance
    out = draw_ramen()
    out.save("entry-ramen.png", optimize=True)
    out.save("entry-ramen.jpg", quality=90, optimize=True)
    # Final grade: a touch more colour, so yolks and broth pop.
    final = ImageEnhance.Color(out).enhance(1.07)
    final.save("entry-ramen-final.jpg", quality=90, optimize=True)
    import os
    print("saved entry-ramen.png", out.size,
          os.path.getsize("entry-ramen.png"), "bytes;",
          "jpg", os.path.getsize("entry-ramen.jpg"), "bytes;",
          "final", os.path.getsize("entry-ramen-final.jpg"), "bytes")
