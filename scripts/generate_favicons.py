"""Generate favicon PNG sizes from a procedural source.

Writes:
  web/public/favicon-32.png    (search results, browser tabs)
  web/public/favicon-192.png   (Android Chrome)
  web/public/favicon-512.png   (Android splash)
  web/public/apple-touch-icon.png  (180x180 for iOS)

The visual identity is the same as og-image.png: cream background, black
"H" wordmark, orange accent marker.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed; skipping favicon generation.", file=sys.stderr)
    sys.exit(0)


PUBLIC = Path(__file__).resolve().parent.parent / "web" / "public"
PUBLIC.mkdir(parents=True, exist_ok=True)

BG = (17, 17, 20)         # ink black background looks crisp at favicon scale
FG = (241, 239, 233)      # cream foreground
ACCENT = (194, 84, 42)


def _pick_font(size: int) -> ImageFont.FreeTypeFont:
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render(size: int, out: Path) -> None:
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)

    # H wordmark — block-letter rendition (procedural, font-independent).
    pad = max(2, size // 6)
    bar_w = max(2, size // 8)
    crossbar_h = max(2, size // 12)
    left_x = pad
    right_x = size - pad
    # Left vertical bar
    draw.rectangle((left_x, pad, left_x + bar_w, size - pad), fill=FG)
    # Right vertical bar
    draw.rectangle((right_x - bar_w, pad, right_x, size - pad), fill=FG)
    # Crossbar
    cy = size // 2 - crossbar_h // 2
    draw.rectangle((left_x, cy, right_x, cy + crossbar_h), fill=FG)
    # Accent dot bottom-right (signature outbreak marker)
    dot_r = max(2, size // 9)
    cx, cy_dot = right_x + 0, size - pad - dot_r
    # nudge dot slightly inset
    cx -= dot_r // 3
    draw.ellipse((cx - dot_r, cy_dot - dot_r, cx + dot_r, cy_dot + dot_r), fill=ACCENT)

    img.save(out, "PNG", optimize=True)
    print(f"OK · wrote {out} ({out.stat().st_size:,} bytes)")


render(32,  PUBLIC / "favicon-32.png")
render(192, PUBLIC / "favicon-192.png")
render(512, PUBLIC / "favicon-512.png")
render(180, PUBLIC / "apple-touch-icon.png")
