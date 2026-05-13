"""Generate the social-share Open Graph image at web/public/og-image.png.

Standalone: requires only Pillow. Produces a 1200x630 PNG matching the
HORIZON visual identity (cream background, ink-black headlines, accent
orange marker). Run any time the branding changes:

    python scripts/generate_og_image.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed; skipping og-image generation.", file=sys.stderr)
    print("Install:  pip install Pillow", file=sys.stderr)
    sys.exit(0)


OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "og-image.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1200, 630
BG = (241, 239, 233)          # cream
INK = (17, 17, 20)             # near-black
MUTED = (90, 90, 96)
ACCENT = (194, 84, 42)         # signature orange

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


def _pick_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """Try a sequence of common system font paths, fall back to default."""
    candidates = []
    if weight == "bold":
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


# Top accent bar
draw.rectangle((0, 0, W, 12), fill=ACCENT)

# HORIZON wordmark (top left)
brand_font = _pick_font(34, "bold")
draw.text((60, 56), "HORIZON", fill=INK, font=brand_font)
sub_font = _pick_font(18, "regular")
draw.text((232, 64), "· hantavirus.software", fill=MUTED, font=sub_font)

# Big headline
h1_font = _pick_font(76, "bold")
draw.text((60, 160), "Live Hantavirus", fill=INK, font=h1_font)
draw.text((60, 244), "Outbreak Tracker", fill=INK, font=h1_font)

# Subhead lead
lead_font = _pick_font(26, "regular")
lead = ("WHO  ·  CDC  ·  ECDC  ·  PAHO  ·  ProMED  ·  peer-reviewed literature")
draw.text((60, 360), lead, fill=MUTED, font=lead_font)

# Provenance tagline
prov_font = _pick_font(22, "regular")
draw.text((60, 420), "Audit-grade source provenance: ICD 206 · NATO Admiralty Scale", fill=INK, font=prov_font)
draw.text((60, 454), "Dual confidence model · Berkeley Protocol chain-of-custody", fill=INK, font=prov_font)

# Footer: CC BY 4.0 + operator
foot_font = _pick_font(18, "regular")
draw.text((60, 540), "Open data, CC BY 4.0  ·  Operated by 79th Unit Limited (UK)", fill=MUTED, font=foot_font)

# Right-side decorative outbreak marker dot
cx, cy, r = W - 220, H // 2 - 30, 90
for ring, alpha in [(r + 28, 60), (r + 14, 110), (r, 220)]:
    rr, gg, bb = ACCENT
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((cx - ring, cy - ring, cx + ring, cy + ring), fill=(rr, gg, bb, alpha))
    img.paste(overlay, (0, 0), overlay)

# Bottom accent bar
draw.rectangle((0, H - 8, W, H), fill=INK)

img.save(OUT, "PNG", optimize=True)
print(f"OK · wrote {OUT} ({OUT.stat().st_size:,} bytes)")
