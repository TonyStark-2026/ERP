# -*- coding: utf-8 -*-
"""
生成 PWA 图标（192x192、512x512 PNG）
优先使用Pillow；如果没装，退回用纯Python生成最小可用的PNG
"""
import os

ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "icons")
os.makedirs(ICON_DIR, exist_ok=True)

SIZES = [192, 512]
# 颜色：蓝白渐变风格
BG_COLOR_TOP = (30, 60, 114)   # #1e3c72
BG_COLOR_BOTTOM = (42, 82, 152) # #2a5298
ICON_TEXT_COLOR = (255, 255, 255)


def with_pillow():
    from PIL import Image, ImageDraw, ImageFont
    for size in SIZES:
        img = Image.new("RGBA", (size, size), BG_COLOR_TOP + (255,))
        draw = ImageDraw.Draw(img)
        # 简易垂直渐变（一行行画）
        for y in range(size):
            t = y / max(1, size - 1)
            r = int(BG_COLOR_TOP[0] * (1 - t) + BG_COLOR_BOTTOM[0] * t)
            g = int(BG_COLOR_TOP[1] * (1 - t) + BG_COLOR_BOTTOM[1] * t)
            b = int(BG_COLOR_TOP[2] * (1 - t) + BG_COLOR_BOTTOM[2] * t)
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        # 画圆环装饰
        margin = int(size * 0.08)
        draw.ellipse([margin, margin, size - margin, size - margin],
                     outline=(255, 255, 255, 80), width=max(2, size // 80))
        draw.ellipse([margin * 2, margin * 2, size - margin * 2, size - margin * 2],
                     outline=(255, 255, 255, 40), width=max(1, size // 160))
        # 写"ERP"三个字母（用默认字体或PIL内置字体）
        text = "ERP"
        try:
            font = ImageFont.truetype("arialbd.ttf", int(size * 0.36))
        except Exception:
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\msyhbd.ttc", int(size * 0.34))
            except Exception:
                font = ImageFont.load_default()
        # 居中文字
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
                  text, fill=ICON_TEXT_COLOR + (255,), font=font)
        out = os.path.join(ICON_DIR, f"icon-{size}.png")
        img.save(out, "PNG")
        print(f"  ✅ 生成 {size}x{size} 图标: {out}")
    return True


def fallback_no_pillow():
    """不用Pillow，生成纯蓝色简单PNG（纯色+简单像素点标记）"""
    import struct, zlib
    def make_png(path, size):
        raw = bytearray()
        for y in range(size):
            raw.append(0)  # filter: None
            t = y / max(1, size - 1)
            r = int(BG_COLOR_TOP[0] * (1 - t) + BG_COLOR_BOTTOM[0] * t)
            g = int(BG_COLOR_TOP[1] * (1 - t) + BG_COLOR_BOTTOM[1] * t)
            b = int(BG_COLOR_TOP[2] * (1 - t) + BG_COLOR_BOTTOM[2] * t)
            for _ in range(size):
                raw.extend([r, g, b, 255])
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        sig = b"\x89PNG\r\n\x1a\n"
        ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # RGBA 8bit
        idat = zlib.compress(bytes(raw), 9)
        with open(path, "wb") as f:
            f.write(sig)
            f.write(chunk(b"IHDR", ihdr))
            f.write(chunk(b"IDAT", idat))
            f.write(chunk(b"IEND", b""))
    for s in SIZES:
        p = os.path.join(ICON_DIR, f"icon-{s}.png")
        make_png(p, s)
        print(f"  ✅ [无Pillow] 生成 {s}x{s} 图标: {p}")
    return True


def main():
    print("🖼️  正在生成PWA应用图标...")
    try:
        with_pillow()
    except ImportError:
        print("  ℹ️  未安装Pillow，使用回退方案生成纯色图标")
        fallback_no_pillow()
    print("✅ 图标生成完成\n")


if __name__ == "__main__":
    main()
