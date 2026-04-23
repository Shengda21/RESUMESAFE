import os
from PIL import Image, ImageDraw, ImageFont


def make_icon(out="assets/icon.ico"):
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Gradient background: #006A60 → #00897B (top to bottom)
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / (size - 1)
        g = int(0x6A + (0x89 - 0x6A) * t)
        b = int(0x60 + (0x7B - 0x60) * t)
        bg_draw.line([(0, y), (size - 1, y)], fill=(0, g, b, 255))

    # Squircle mask
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(0, 0), (size - 1, size - 1)], radius=96, fill=255
    )
    img.paste(bg, (0, 0), mask)

    # Letter "历" centered in white
    draw = ImageDraw.Draw(img)
    letter = "历"
    font_size = int(size * 0.52)
    font = None
    candidates = [
        "NotoSansSC-Bold.ttf",
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "msyh.ttc"),
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "msyhbd.ttc"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - w) // 2 - bbox[0], (size - h) // 2 - bbox[1]),
        letter,
        fill=(255, 255, 255, 255),
        font=font,
    )

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(
        out,
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"图标已生成：{out}")


if __name__ == "__main__":
    make_icon()
