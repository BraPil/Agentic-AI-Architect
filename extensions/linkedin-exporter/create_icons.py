#!/usr/bin/env python3
"""
Generate simple placeholder icons for the Chrome extension.
Run once: python3 create_icons.py
Requires: pip install Pillow
"""
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    print("Or use any 16x16, 48x48, 128x128 PNG files named icon16.png, icon48.png, icon128.png")
    raise

from pathlib import Path

HERE = Path(__file__).parent

def make_icon(size: int) -> None:
    img = Image.new("RGBA", (size, size), (0, 119, 181, 255))  # LinkedIn blue
    draw = ImageDraw.Draw(img)
    # Draw a white "A" (AAA)
    font_size = max(8, size // 2)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    text = "A"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    img.save(HERE / f"icon{size}.png")
    print(f"Created icon{size}.png")

for s in (16, 48, 128):
    make_icon(s)
