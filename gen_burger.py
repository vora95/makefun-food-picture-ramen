"""Draw a gourmet burger, procedurally, with PIL + numpy.

No photo, no external assets, no paid service: every pixel is computed here.
Renders at 2x (2048) and downsamples to 1024 for smooth edges.
Output: entry-burger.png (1024x1024, < 1 MiB).
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2                      # supersample factor
W = H = 1024 * SS           # working canvas
OUT = 1024
rng = random.Random(20261114)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def radial_bg(size, center, inner, mid, outer):
    """Warm dark radial glow background, built small then upscaled."""
    s = 256
    yy, xx = np.mgrid[0:s, 0:s]
    cx, cy = center[0] / size * s, center[1] / size * s
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (s * 0.62)
    d = np.clip(d, 0, 1)
    inner = np.array(inner, float)
    mid = np.array(mid, float)
    outer = np.array(outer, float)
    # two-stop blend: inner->mid for d<0.55, mid->outer after
    t1 = np.clip(d / 0.55, 0, 1)[..., None]
    t2 = np.clip((d - 0.55) / 0.45, 0, 1)[..., None]
    col = inner * (1 - t1) + mid * t1
    col = col * (1 - t2) + outer * t2
    img = Image.fromarray(col.astype(np.uint8), "RGB").resize((size, size), Image.BICUBIC)
    return img


def vgrad(w, h, top, bottom):
    """Vertical gradient, built small then upscaled."""
    s = 256
    t = np.linspace(0, 1, s)[:, None, None]
    top = np.array(top, float)
    bottom = np.array(bottom, float)
    col = top * (1 - t) + bottom * t
    col = np.repeat(col, 4, axis=1)
    img = Image.fromarray(col.astype(np.uint8), "RGB").resize((w, h), Image.BICUBIC)
    return img


def soft_layer(size, draw_fn, blur):
    """Draw on a transparent layer, blur it, return the layer."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    draw_fn(d)
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return layer


def radial_patch(w, h, cx, cy, radius, inner, outer):
    """Small radial gradient patch (light centre -> darker edge), upscaled."""
    s = 128
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt(((xx - cx / w * s) ** 2 + (yy - cy / h * s) ** 2)) / (radius / w * s)
    d = np.clip(d, 0, 1)[..., None]
    col = np.array(inner, float) * (1 - d) + np.array(outer, float) * d
    return Image.fromarray(col.astype(np.uint8), "RGB").resize((w, h), Image.BICUBIC)


def wavy_band(d, x0, x1, y_top, y_bot, amp, waves, fill, step=8):
    """A horizontal band whose bottom edge waves like lettuce / cheese drip."""
    pts_top = [(x, y_top) for x in range(x0, x1 + 1, step)]
    pts_bot = []
    for x in range(x1, x0 - 1, -step):
        t = (x - x0) / (x1 - x0)
        y = y_bot + amp * math.sin(t * math.pi * 2 * waves)
        pts_bot.append((x, y))
    d.polygon(pts_top + pts_bot, fill=fill)


def dome_points(cx, base_y, rx, top_y, n=80):
    """Points of a bun dome: half-ellipse arc from left base to right base."""
    pts = []
    for i in range(n + 1):
        a = math.pi * (1 - i / n)  # pi -> 0, left -> right over the top
        x = cx + rx * math.cos(a)
        y = base_y - (base_y - top_y) * math.sin(a)
        pts.append((x, y))
    return pts


def draw_burger():
    img = radial_bg(W, (W // 2, int(H * 0.46)), (96, 58, 34), (52, 30, 18), (20, 12, 8))
    img = img.convert("RGBA")

    # ---- soft spotlight behind the burger ---------------------------------
    glow = soft_layer((W, H), lambda d: d.ellipse(
        [W // 2 - 620, 320, W // 2 + 620, 1560], fill=(255, 176, 92, 60)), 180)
    img.alpha_composite(glow)

    # ---- plate shadow on the backdrop --------------------------------------
    img.alpha_composite(soft_layer((W, H), lambda d: d.ellipse(
        [W // 2 - 820, 1420, W // 2 + 820, 1760], fill=(0, 0, 0, 110)), 60))

    # ---- wooden board (warm, seen slightly from above) ----------------------
    board = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd0 = ImageDraw.Draw(board)
    bd0.ellipse([W // 2 - 800, 1330, W // 2 + 800, 1810], fill=(107, 66, 35, 255))
    bd0.ellipse([W // 2 - 800, 1330, W // 2 + 800, 1810], outline=(70, 42, 20, 255), width=6)
    bd0.ellipse([W // 2 - 740, 1370, W // 2 + 740, 1770], fill=(122, 76, 40, 255))
    # wood grain: faint darker arcs
    for gy, gw in [(1420, 700), (1500, 730), (1580, 720), (1660, 680), (1730, 600)]:
        bd0.arc([W // 2 - gw, gy - 60, W // 2 + gw, gy + 60], 200, 340,
                fill=(90, 54, 26, 160), width=5)
    img.alpha_composite(board)

    # ---- fries leaning behind the burger (right side) ----------------------
    # Each fry: vertical gradient + light left edge, tucked behind the burger.
    fries = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, (fx, fy, ang, ln) in enumerate([
            (1400, 1150, -13, 470), (1470, 1120, -7, 510),
            (1540, 1150, -1, 490), (1600, 1200, 6, 420)]):
        stick = Image.new("RGBA", (90, ln), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stick)
        g = vgrad(90, ln, (244, 190, 92), (214, 140, 44))
        smask = Image.new("L", (90, ln), 0)
        smd = ImageDraw.Draw(smask)
        smd.rounded_rectangle([6, 0, 84, ln], radius=18, fill=255)
        stick.paste(g, (0, 0), smask)
        sd.rounded_rectangle([6, 0, 84, ln], radius=18, outline=(178, 108, 26, 255), width=4)
        sd.rectangle([16, 12, 34, ln - 12], fill=(252, 216, 140, 200))
        stick = stick.rotate(ang, expand=True, resample=Image.BICUBIC)
        fries.alpha_composite(stick, (fx, fy))
    img.alpha_composite(fries)

    # ---- burger shadow on the plate ----------------------------------------
    img.alpha_composite(soft_layer((W, H), lambda d: d.ellipse(
        [W // 2 - 520, 1400, W // 2 + 560, 1620], fill=(0, 0, 0, 130)), 40))

    cx = W // 2

    # ---- bottom bun ---------------------------------------------------------
    bun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bun)
    bd.rounded_rectangle([cx - 430, 1400, cx + 430, 1540], radius=70,
                         fill=(198, 128, 46, 255))
    bd.rounded_rectangle([cx - 430, 1400, cx + 430, 1540], radius=70,
                         outline=(146, 88, 26, 255), width=5)
    # crumb highlight on the top edge of the bottom bun
    bd.rounded_rectangle([cx - 420, 1400, cx + 420, 1445], radius=40,
                         fill=(226, 164, 84, 255))
    img.alpha_composite(bun)

    # ---- patty (thick, charred, juicy: vertical gradient + char + sheen) -----
    patty = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd2 = ImageDraw.Draw(patty)
    pg = vgrad(960, 160, (122, 74, 32), (58, 30, 12))
    pmask = Image.new("L", (W, H), 0)
    pmd = ImageDraw.Draw(pmask)
    pmd.rounded_rectangle([cx - 480, 1260, cx + 480, 1420], radius=60, fill=255)
    patty.paste(pg, (cx - 480, 1260), pmask.crop((cx - 480, 1260, cx + 480, 1420)))
    pd2.rounded_rectangle([cx - 480, 1260, cx + 480, 1420], radius=60,
                          outline=(40, 20, 8, 255), width=5)
    # char speckles
    for _ in range(200):
        x = rng.randint(cx - 470, cx + 470)
        y = rng.randint(1270, 1410)
        r = rng.randint(2, 6)
        c = rng.choice([(36, 18, 8, 190), (150, 92, 44, 170)])
        pd2.ellipse([x - r, y - r, x + r, y + r], fill=c)
    # juicy sheen on the top edge
    pd2.rounded_rectangle([cx - 460, 1260, cx + 460, 1286], radius=26,
                          fill=(168, 104, 48, 150))
    img.alpha_composite(patty)

    # ---- cheese: molten band with drips over the patty ----------------------
    cheese = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cheese)
    cg = vgrad(940, 130, (255, 196, 77), (240, 150, 18))
    cmask = Image.new("L", (W, H), 0)
    cmd = ImageDraw.Draw(cmask)
    wavy_band(cmd, cx - 470, cx + 470, 1170, 1280, 26, 5, 255)
    cheese.paste(cg, (cx - 470, 1170), cmask.crop((cx - 470, 1170, cx + 470, 1300)))
    # drips
    for dx, dl in [(-330, 150), (-90, 110), (150, 165), (360, 120)]:
        x = cx + dx
        cd.rounded_rectangle([x - 34, 1240, x + 34, 1240 + dl], radius=32,
                             fill=(246, 168, 33, 255))
        cd.ellipse([x - 34, 1240 + dl - 34, x + 34, 1240 + dl + 34],
                   fill=(246, 168, 33, 255))
    # cheese gloss
    cd.rectangle([cx - 440, 1170, cx + 440, 1192], fill=(255, 214, 110, 190))
    img.alpha_composite(cheese)

    # ---- tomato slice --------------------------------------------------------
    tom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tom)
    tg = vgrad(880, 75, (226, 84, 60), (196, 44, 30))
    tmask = Image.new("L", (W, H), 0)
    tmd = ImageDraw.Draw(tmask)
    tmd.rounded_rectangle([cx - 440, 1110, cx + 440, 1185], radius=36, fill=255)
    tom.paste(tg, (cx - 440, 1110), tmask.crop((cx - 440, 1110, cx + 440, 1185)))
    td.rounded_rectangle([cx - 440, 1110, cx + 440, 1185], radius=36,
                         outline=(150, 28, 20, 255), width=4)
    td.rounded_rectangle([cx - 420, 1110, cx + 420, 1136], radius=20,
                         fill=(240, 120, 92, 190))
    img.alpha_composite(tom)

    # ---- lettuce frill --------------------------------------------------------
    letc = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(letc)
    wavy_band(ld, cx - 500, cx + 500, 1050, 1130, 30, 7, (88, 156, 52, 255))
    wavy_band(ld, cx - 470, cx + 470, 1050, 1108, 18, 7, (126, 198, 82, 255))
    # veins: short darker arcs along the frill
    for vx in range(cx - 460, cx + 460, 90):
        ld.arc([vx, 1052, vx + 70, 1120], 20, 160, fill=(64, 124, 36, 220), width=4)
    img.alpha_composite(letc)

    # ---- creamy sauce drip (right side) ---------------------------------------
    sauce = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sauce)
    sd.rounded_rectangle([cx + 306, 1060, cx + 362, 1290], radius=28,
                         fill=(243, 223, 158, 255))
    sd.ellipse([cx + 306, 1262, cx + 362, 1318], fill=(243, 223, 158, 255))
    sd.rectangle([cx + 312, 1070, cx + 330, 1280], fill=(252, 240, 196, 200))
    img.alpha_composite(sauce)

    # ---- top bun dome ----------------------------------------------------------
    # Radial light: bright warm top-left, deep golden at the rim.
    dome = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dome)
    grad = radial_patch(900, 480, 330, 150, 560, (250, 196, 120), (188, 112, 34))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    pts = dome_points(cx, 1080, 450, 600)
    md.polygon(pts + [(cx + 450, 1080), (cx - 450, 1080)], fill=255)
    dome.paste(grad, (cx - 450, 600), mask.crop((cx - 450, 600, cx + 450, 1080)))
    # darker crust band hugging the dome base
    dd.polygon(pts + [(cx + 450, 1080), (cx - 450, 1080)],
               outline=(146, 86, 24, 255), width=6)
    # baked crumb speckle, faint
    for _ in range(160):
        x = rng.randint(cx - 430, cx + 430)
        y = rng.randint(620, 1060)
        r = rng.randint(2, 5)
        dd.ellipse([x - r, y - r, x + r, y + r],
                   fill=rng.choice([(214, 140, 52, 120), (240, 180, 96, 120)]))
    img.alpha_composite(dome)

    # ---- sesame seeds -----------------------------------------------------------
    seeds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd2 = ImageDraw.Draw(seeds)
    seed_spots = [(760, 760), (880, 690), (1010, 660), (1150, 700), (1270, 770),
                  (830, 830), (960, 800), (1100, 830), (1210, 890), (900, 900),
                  (1050, 880), (1180, 950), (800, 920), (1330, 860)]
    for sx, sy in seed_spots:
        ang = rng.uniform(-40, 40)
        seed = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
        sdd = ImageDraw.Draw(seed)
        sdd.ellipse([4, 4, 60, 36], fill=(255, 233, 176, 255))
        sdd.ellipse([4, 4, 60, 36], outline=(214, 164, 96, 255), width=3)
        seed = seed.rotate(ang, expand=True, resample=Image.BICUBIC)
        seeds.alpha_composite(seed, (sx - 32, sy - 20))
    img.alpha_composite(seeds)

    # ---- gloss highlight on the dome ---------------------------------------------
    img.alpha_composite(soft_layer((W, H), lambda d: d.ellipse(
        [cx - 330, 640, cx + 40, 830], fill=(255, 240, 210, 90)), 50))

    # ---- scattered sesame on the board -------------------------------------------
    props = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    prd = ImageDraw.Draw(props)
    for px, py in [(700, 1560), (760, 1610), (1420, 1580), (1360, 1640), (640, 1660)]:
        prd.ellipse([px, py, px + 26, py + 16], fill=(255, 233, 176, 255))
    img.alpha_composite(props)

    # ---- grade: warm, a touch more colour + contrast ------------------------------
    img = img.convert("RGB")
    img = img.resize((OUT, OUT), Image.LANCZOS)

    # ---- grain + vignette (at final size, subtle) ---------------------------------
    arr = np.asarray(img).astype(np.float32)
    noise = np.random.default_rng(7).normal(0, 3.0, arr.shape[:2])
    arr += noise[..., None]
    yy, xx = np.mgrid[0:OUT, 0:OUT]
    d = np.sqrt(((xx - OUT / 2) / (OUT * 0.72)) ** 2 + ((yy - OUT / 2) / (OUT * 0.72)) ** 2)
    vig = np.clip(1 - 0.22 * np.clip(d - 0.55, 0, 1) ** 2, 0, 1)
    arr *= vig[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    return img


if __name__ == "__main__":
    out = draw_burger()
    out.save("entry-burger.png", optimize=True)
    out.save("entry-burger.jpg", quality=90, optimize=True)
    import os
    print("saved entry-burger.png", out.size,
          os.path.getsize("entry-burger.png"), "bytes;",
          "jpg", os.path.getsize("entry-burger.jpg"), "bytes")
