# -*- coding: utf-8 -*-
"""
双场景二维码生成脚本
场景A：WiFi版 (192.168.3.93:8000)
场景B：移动热点版 (192.168.137.1:8000)
"""
import qrcode
import os
import struct
from PIL import Image, ImageDraw, ImageFont

# -------- 配置 --------
URL_A = "http://192.168.3.93:8000/"
URL_B = "http://192.168.137.1:8000/"

TITLE_A = "【主-推荐】WiFi版扫码"
SUBTITLE_A = "手机连同一WiFi → 扫此码"
TITLE_B = "【备】连电脑热点版扫码"
SUBTITLE_B = "手机连电脑热点 → 扫此码"
COMPAT_TITLE_A = "兼容版 · 主码 WiFi (A)"
COMPAT_SUB_A = "主链接: http://192.168.3.93:8000/\n备用: http://192.168.137.1:8000/"
COMPAT_TITLE_B = "兼容版 · 备码 热点 (B)"
COMPAT_SUB_B = "主链接: http://192.168.3.93:8000/\n备用: http://192.168.137.1:8000/"

OUTPUTS_A = [
    r"C:\Users\ruancanling\Desktop\【主-推荐】手机扫码-WiFi版.png",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\【主-推荐】手机扫码-WiFi版.png",
    r"C:\Users\ruancanling\Desktop\exam work\【主-推荐】手机扫码-WiFi版.png",
]

OUTPUTS_B = [
    r"C:\Users\ruancanling\Desktop\【备】手机扫码-连电脑热点版.png",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\【备】手机扫码-连电脑热点版.png",
    r"C:\Users\ruancanling\Desktop\exam work\【备】手机扫码-连电脑热点版.png",
]

OUTPUTS_COMPAT_A = [
    r"C:\Users\ruancanling\Desktop\兼容版-A-WiFi主码_含双链接说明.png",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\兼容版-A-WiFi主码_含双链接说明.png",
]
OUTPUTS_COMPAT_B = [
    r"C:\Users\ruancanling\Desktop\兼容版-B-热点备码_含双链接说明.png",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\兼容版-B-热点备码_含双链接说明.png",
]


def get_font(size=28, bold=False):
    """尝试获取中文字体"""
    font_candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for f in font_candidates:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return ImageFont.load_default()


def measure_text(draw_obj, text, font):
    """兼容 Pillow 10.x：用 textbbox 计算文字宽高"""
    bbox = draw_obj.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    return w, h


def make_qr_image(url, title, subtitle, qr_box_size=12, border=4, img_w=800):
    """生成带标题说明的二维码大图"""
    # 生成纯二维码
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=qr_box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # 计算整体画布高度
    title_font = get_font(36, bold=True)
    sub_font = get_font(24, bold=False)
    url_font = get_font(20, bold=False)

    # 使用 ImageDraw 测量文字
    tmp_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    _, th = measure_text(tmp_draw, title, title_font)
    sub_lines = subtitle.split("\n")
    sub_heights = []
    for line in sub_lines:
        _, sh = measure_text(tmp_draw, line, sub_font)
        sub_heights.append(sh)
    _, uh = measure_text(tmp_draw, url, url_font)

    padding = 30
    qr_size = min(img_w - 2 * padding, qr_img.size[0])
    qr_img = qr_img.resize((qr_size, qr_size), Image.NEAREST)

    total_h = padding + th + 10 + sum(sub_heights) + len(sub_heights) * 5 + 20 + qr_size + 20 + uh + padding + 10
    canvas = Image.new("RGBA", (img_w, total_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    y = padding
    # 标题居中
    tw, _ = measure_text(draw, title, title_font)
    draw.text(((img_w - tw) / 2, y), title, fill=(30, 30, 120, 255), font=title_font)
    y += th + 10

    # 副标题
    for i, line in enumerate(sub_lines):
        sw, _ = measure_text(draw, line, sub_font)
        draw.text(((img_w - sw) / 2, y), line, fill=(80, 80, 80, 255), font=sub_font)
        y += sub_heights[i] + 5

    y += 15
    # 二维码居中
    canvas.paste(qr_img, ((img_w - qr_size) // 2, y))
    y += qr_size + 20

    # URL 底部
    uw, _ = measure_text(draw, url, url_font)
    draw.text(((img_w - uw) / 2, y), url, fill=(150, 50, 50, 255), font=url_font)

    return canvas


def save_and_report(img, paths):
    """保存图片并返回报告信息"""
    reports = []
    for p in paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p, format="PNG")
        size = os.path.getsize(p)
        exists = os.path.exists(p)
        is_png = check_png_valid(p)
        reports.append({
            "path": p,
            "exists": exists,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2),
            "valid_png": is_png,
        })
    return reports


def check_png_valid(filepath):
    """检查文件是否为合法 PNG（PNG 签名 + IHDR 块）"""
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)
            # PNG 签名: 89 50 4E 47 0D 0A 1A 0A
            if header != b"\x89PNG\r\n\x1a\n":
                return False
            # 读 IHDR
            length_data = f.read(4)
            if len(length_data) < 4:
                return False
            length = struct.unpack(">I", length_data)[0]
            chunk_type = f.read(4)
            if chunk_type != b"IHDR":
                return False
            # 再用 PIL 验证
            with Image.open(filepath) as im:
                im.verify()
            return True
    except Exception as e:
        return f"ERROR:{e}"


def main():
    all_reports = []

    # 场景 A
    print("=" * 60)
    print("生成场景 A (WiFi版) 二维码 ...")
    img_a = make_qr_image(URL_A, TITLE_A, SUBTITLE_A + "\n扫码后浏览器打开 ERP 智能系统登录页")
    rep_a = save_and_report(img_a, OUTPUTS_A)
    all_reports.extend(rep_a)

    # 场景 B
    print("=" * 60)
    print("生成场景 B (热点版) 二维码 ...")
    img_b = make_qr_image(URL_B, TITLE_B, SUBTITLE_B + "\n扫码后浏览器打开 ERP 智能系统登录页")
    rep_b = save_and_report(img_b, OUTPUTS_B)
    all_reports.extend(rep_b)

    # 兼容版 A (A 二维码 + A+B 链接说明)
    print("=" * 60)
    print("生成兼容版 A (含双链接说明, 主码WiFi) ...")
    img_ca = make_qr_image(URL_A, COMPAT_TITLE_A, COMPAT_SUB_A)
    rep_ca = save_and_report(img_ca, OUTPUTS_COMPAT_A)
    all_reports.extend(rep_ca)

    # 兼容版 B (B 二维码 + A+B 链接说明)
    print("=" * 60)
    print("生成兼容版 B (含双链接说明, 备码热点) ...")
    img_cb = make_qr_image(URL_B, COMPAT_TITLE_B, COMPAT_SUB_B)
    rep_cb = save_and_report(img_cb, OUTPUTS_COMPAT_B)
    all_reports.extend(rep_cb)

    # 打印报告
    print("\n" + "=" * 80)
    print("【二维码生成验证报告】")
    print("=" * 80)
    for i, r in enumerate(all_reports, 1):
        status_icon = "✅" if r["exists"] and r["valid_png"] is True else "❌"
        png_info = "合法PNG" if r["valid_png"] is True else f"异常: {r['valid_png']}"
        print(f"\n[{i}] {status_icon} {r['path']}")
        print(f"    存在: {r['exists']}  |  大小: {r['size_bytes']} B ({r['size_kb']} KB)  |  PNG: {png_info}")

    total_ok = sum(1 for r in all_reports if r["exists"] and r["valid_png"] is True)
    print("\n" + "-" * 80)
    print(f"总计: {len(all_reports)} 个文件, 成功 {total_ok} 个, 失败 {len(all_reports)-total_ok} 个")
    print("=" * 80)


if __name__ == "__main__":
    main()
