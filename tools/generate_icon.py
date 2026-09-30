"""
Generate professional high-resolution application icon (ICO & PNG).
Includes multiple icon sizes: 16, 24, 32, 48, 64, 128, 256.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def make_icon():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(out_dir, exist_ok=True)
    ico_path = os.path.join(out_dir, "icon.ico")
    png_path = os.path.join(out_dir, "icon.png")

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Rounded rectangle background with smooth gradient
    corner_radius = 52
    for y in range(size):
        # Vertical gradient from deep cobalt #1e40af to vibrant royal #3b82f6
        t = y / float(size)
        r = int(30 * (1 - t) + 37 * t)
        g = int(64 * (1 - t) + 99 * t)
        b = int(175 * (1 - t) + 235 * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Mask with rounded corners
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=corner_radius, fill=255)

    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.paste(img, (0, 0), mask=mask)
    draw = ImageDraw.Draw(base)

    # Subtle inner border for glass/metallic feel
    draw.rounded_rectangle([2, 2, size - 3, size - 3], radius=corner_radius - 1, outline=(255, 255, 255, 70), width=3)

    # 2. Modern Play Triangle + Dynamic Sync Wave symbol
    # Triangle
    cx, cy = 128, 122
    poly = [
        (cx - 36, cy - 48),
        (cx - 36, cy + 48),
        (cx + 48, cy)
    ]
    # Drop shadow
    shadow_poly = [(x + 2, y + 4) for (x, y) in poly]
    draw.polygon(shadow_poly, fill=(15, 23, 42, 120))
    # Main white shape
    draw.polygon(poly, fill=(255, 255, 255, 250))

    # Inner cut / accent
    poly_inner = [
        (cx - 16, cy - 20),
        (cx - 16, cy + 20),
        (cx + 20, cy)
    ]
    draw.polygon(poly_inner, fill=(37, 99, 235, 255))

    # 3. Label "AUTO" bar at bottom
    bar_y = 194
    draw.rounded_rectangle([42, bar_y, 214, bar_y + 34], radius=10, fill=(15, 23, 42, 220), outline=(255, 255, 255, 60), width=1)
    
    # Try default font or basic text
    try:
        font = ImageFont.truetype("arialbd.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    draw.text((128, bar_y + 16), "AUTOCAPCUT", fill=(255, 255, 255, 250), font=font, anchor="mm")

    # Save PNG
    base.save(png_path, "PNG")

    # Save multi-resolution ICO
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    base.save(ico_path, format="ICO", sizes=sizes)
    print(f"Icon created successfully: {ico_path}")

if __name__ == '__main__':
    make_icon()
