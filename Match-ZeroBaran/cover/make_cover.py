"""Cover art generator — 1600x1000 product/documentation cover.

    python3 cover/make_cover.py      # -> cover/cover.png

Fonts are downloaded once by `cover/fetch_fonts.sh` (or manually) into
cover/fonts/ and are git-ignored; the script falls back to DejaVu otherwise.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
W, H = 1600, 1000

BG_TOP = (10, 16, 32)
BG_BOTTOM = (22, 12, 52)
ACCENT = (0, 229, 181)
ACCENT2 = (255, 176, 32)
WHITE = (245, 247, 252)
MUTED = (150, 162, 190)
CARD = (18, 26, 48)

AR_BOLD = FONTS / "Tajawal-Bold.ttf"
AR_REG = FONTS / "Tajawal-Regular.ttf"
EN_BOLD = FONTS / "Poppins-Bold.ttf"
EN_SEMI = FONTS / "Poppins-SemiBold.ttf"

FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        try:
            return ImageFont.truetype(FALLBACK, size)
        except OSError:
            return ImageFont.load_default()


def gradient() -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def network_overlay(img: Image.Image) -> None:
    """A quiet node/edge mesh in the corner = 'matching engine'."""
    import math
    import random

    random.seed(31)
    d = ImageDraw.Draw(img, "RGBA")
    nodes = []
    for i in range(46):
        x = 980 + int(math.cos(i * 1.7) * (120 + (i % 7) * 46)) + random.randint(-40, 40)
        y = 700 + int(math.sin(i * 2.3) * (90 + (i % 5) * 40)) + random.randint(-30, 30)
        nodes.append((x, y))
    for i, a in enumerate(nodes):
        for b in nodes[i + 1 :]:
            dist = math.hypot(a[0] - b[0], a[1] - b[1])
            if dist < 170:
                alpha = int(max(0, 110 - dist / 2.2))
                d.line([a, b], fill=(0, 229, 181, alpha), width=2)
    for i, n in enumerate(nodes):
        r = 5 + (i % 4)
        color = ACCENT2 if i % 6 == 0 else ACCENT
        d.ellipse([n[0] - r, n[1] - r, n[0] + r, n[1] + r], fill=(*color, 210))


def badge(d: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt, fill, pad=(18, 10)) -> tuple[int, int, int, int]:
    box = d.textbbox((0, 0), text, font=fnt)
    w, h = box[2] - box[0], box[3] - box[1]
    rect = [x, y, x + w + pad[0] * 2, y + h + pad[1] * 2]
    d.rounded_rectangle(rect, radius=14, fill=(255, 255, 255, 14), outline=(*ACCENT, 90), width=2)
    d.text((x + pad[0], y + pad[1] - box[1]), text, font=fnt, fill=fill)
    return tuple(rect)


def main() -> None:
    img = gradient()
    network_overlay(img)
    d = ImageDraw.Draw(img, "RGBA")

    # top rule
    d.rectangle([0, 0, W, 8], fill=(*ACCENT, 255))
    d.rectangle([0, H - 6, W, H], fill=(*ACCENT2, 255))

    x = 90
    y = 78

    # eyebrow
    f_eyebrow = font(EN_SEMI, 30)
    d.text((x + 4, y), "100% FREE STACK  ·  PYTHON  ·  SCIKIT-LEARN  ·  SUPABASE  ·  GEMINI  ·  TELEGRAM",
           font=f_eyebrow, fill=ACCENT)
    y += 56

    # Latin title
    f_title = font(EN_BOLD, 96)
    d.text((x, y), "Match-ZeroBaran", font=f_title, fill=WHITE)
    y += 128

    # Arabic title
    f_ar = font(AR_BOLD, 78)
    d.text((x, y), "المنظومة الذاتية الذكية", font=f_ar, fill=ACCENT2)
    y += 104
    d.text((x, y), "لمحركات التوصية والتخصيص والبيع المتقاطع", font=f_ar, fill=WHITE)
    y += 128

    # tagline
    f_tag = font(AR_REG, 40)
    d.text((x, y), "ترفع متوسط قيمة السلة (AOV) — دون دفع سنت واحد لأي أداة مدفوعة.",
           font=f_tag, fill=MUTED)
    y += 78

    # feature pills
    f_pill = font(AR_REG, 32)
    pills = [
        "تشابه جيب التتبّع (Cosine)",
        "سلال تسوق (Market Basket)",
        "صياغة تسويقية بالذكاء الاصطناعي",
        "لوحة تحكم + تليجرام",
    ]
    cx = x
    for i, p in enumerate(pills):
        rect = badge(d, cx, y, p, f_pill, WHITE)
        if i == 0:
            top, bottom = rect[1], rect[3]
        cx = rect[2] + 18
        if cx > 1180:
            cx = x
            y += (bottom - top) + 18
    y = (bottom + 74) if cx <= 1180 else y + 110

    # layered architecture chips
    f_chip = font(EN_SEMI, 30)
    layers = ["1  Ingest & Similarity", "2  AI Matching Brain", "3  Persistence", "4  Delivery"]
    cx = x
    for i, l in enumerate(layers):
        col = ACCENT if i % 2 == 0 else ACCENT2
        box = d.textbbox((0, 0), l, font=f_chip)
        w = box[2] - box[0] + 40
        rect = [cx, y, cx + w, y + 62]
        d.rounded_rectangle(rect, radius=16, fill=(255, 255, 255, 16), outline=(*col, 160), width=2)
        d.text((cx + 20, y + 26 - box[1]), l, font=f_chip, fill=col)
        cx += w + 16
    y += 100

    # footer: rights + support
    f_small = font(AR_REG, 30)
    footer = "المؤلف: Baran Avisat  ·  baranavisat@gmail.com  ·  واتساب 00905313263722  ·  © 2026 جميع الحقوق محفوظة"
    d.text((x, H - 74), footer, font=f_small, fill=MUTED)
    d.text((x, H - 112), "⚖️ رخصة الاستخدام الشخصي والتجاري داخل مشترياتك — يُمنع إعادة بيع الكود كاملاً.",
           font=f_small, fill=(200, 205, 220))

    # stamp
    stamp = "v1.0 · Zero-Cost"
    f_stamp = font(EN_SEMI, 34)
    sb = d.textbbox((0, 0), stamp, font=f_stamp)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    sx, sy = W - sw - 80, 74
    d.rounded_rectangle([sx - 22, sy - 16, sx + sw + 22, sy + sh + 20], radius=18,
                        fill=(0, 0, 0, 90), outline=(*ACCENT2, 220), width=3)
    d.text((sx, sy - sb[1]), stamp, font=f_stamp, fill=ACCENT2)

    out = HERE / "cover.png"
    img.save(out, "PNG")
    print(f"✅ {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()