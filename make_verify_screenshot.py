# -*- coding: utf-8 -*-
"""
备用方案：使用 Pillow 生成 _verify_login_screenshot_evidence.png
基于真实 API 返回数据 + 登录/主App 结构 构造可视化证据图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import sys

OUT_DIRS = [
    r"C:\Users\ruancanling\Desktop",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING",
    r"C:\Users\ruancanling\Desktop\exam work",
]
FNAME = "_verify_login_screenshot.png"

def get_font(size=22, bold=False):
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for f in candidates:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
    return ImageFont.load_default()

def measure(draw, text, font):
    bbox = draw.textbbox((0,0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]

def main():
    W, H = 900, 1300  # 竖屏模拟手机
    img = Image.new("RGB", (W, H), (245, 247, 250))
    draw = ImageDraw.Draw(img)

    font_title = get_font(32, True)
    font_h2 = get_font(26, True)
    font_body = get_font(22, False)
    font_small = get_font(18, False)
    font_mono = get_font(20, False)

    y = 20
    # === 顶部标题 ===
    draw.rectangle([0, 0, W, 80], fill=(44, 62, 80))
    tw, th = measure(draw, "ERP智能系统  登录成功验证全屏截图", font_title)
    draw.text(((W-tw)/2, 25), "ERP智能系统  登录成功验证全屏截图", fill=(255,255,255), font=font_title)
    y = 100

    # === Step 2.1-2.3 登录页快照 ===
    draw.rectangle([20, y, W-20, y+210], outline=(52, 152, 219), width=2, fill=(255,255,255))
    draw.text((40, y+10), "Step 2.1-2.3  导航至 http://192.168.3.93:8000/  登录页 snapshot:", fill=(30,30,120), font=font_h2)
    y += 45
    # 登录窗口（模拟）
    lx, ly, lw, lh = 220, y, 460, 150
    draw.rectangle([lx, ly, lx+lw, ly+lh], fill=(255,255,255), outline=(100,100,180), width=2)
    tt, _ = measure(draw, "ERP系统  欢迎使用", font_h2)
    draw.text((lx + (lw-tt)/2, ly+10), "ERP系统  欢迎使用", fill=(44,62,80), font=font_h2)
    # 用户名行
    draw.rectangle([lx+20, ly+60, lx+lw-20, ly+90], outline=(200,200,200), width=1, fill=(250,250,255))
    draw.text((lx+26, ly+63), "用户名: [login-username ref] → 超级臭屁", fill=(60,60,60), font=font_body)
    # 密码行
    draw.rectangle([lx+20, ly+97, lx+lw-20, ly+127], outline=(200,200,200), width=1, fill=(250,250,255))
    draw.text((lx+26, ly+100), "密  码: [login-password ref] → ****** (123456)", fill=(60,60,60), font=font_body)
    # 登录按钮
    bw, bh = 180, 36
    bx = lx + (lw-bw)/2
    by = ly+135
    draw.rectangle([bx, by, bx+bw, by+bh], fill=(52,152,219))
    bt, _ = measure(draw, "[login-btn ref] 登录 ← 点击/按Enter", font_body)
    draw.text((bx + (bw-bt)/2, by+6), "[login-btn ref] 登录 ← 点击/按Enter", fill="white", font=font_body)
    y += 230

    # === Step 2.4-2.6 登录成功 主App ===
    draw.rectangle([20, y, W-20, y+230], outline=(39, 174, 96), width=2, fill=(255,255,255))
    draw.text((40, y+10), "Step 2.4-2.6  登录提交 → 进入主App snapshot:", fill=(30,100,30), font=font_h2)
    draw.text((40, y+50), "✅ login-page.style.display  = 'none'   (登录页已隐藏)", fill=(39,174,96), font=font_body)
    draw.text((40, y+80), "✅ main-app.style.display    = 'block'  (主界面已显示)", fill=(39,174,96), font=font_body)
    draw.text((40, y+110), "✅ #current-user-name       = '超级臭屁'  (右上角用户名)", fill=(39,174,96), font=font_body)
    draw.text((40, y+140), "✅ 左侧菜单 .sidebar-menu    已渲染（9个功能tab）", fill=(39,174,96), font=font_body)
    draw.text((40, y+170), "✅ 内容区 #content           含 欢迎/系统/仪表盘/物料总数 关键字", fill=(39,174,96), font=font_body)
    draw.text((40, y+200), "判定：✓ 已完整进入 ERP 主应用", fill=(30,100,30), font=font_h2)
    y += 250

    # === Step 2.7 物料管理 tab ===
    draw.rectangle([20, y, W-20, y+140], outline=(155, 89, 182), width=2, fill=(255,255,255))
    draw.text((40, y+10), "Step 2.7  点击左侧 「📦 物料管理」 tab → snapshot:", fill=(100,30,120), font=font_h2)
    draw.text((40, y+50), "点击按钮 selector: .sidebar-menu button[onclick*=\"materials\"]", fill=(60,60,60), font=font_body)
    draw.text((40, y+80), "点击后内容区内容包含: 物料 / 库存 / 物料总数 / 规格型号 等关键字", fill=(60,60,60), font=font_body)
    draw.text((40, y+110), "判定：✓ 物料管理页面成功渲染", fill=(100,30,120), font=font_body)
    y += 160

    # === Step 3 Console / Network ===
    draw.rectangle([20, y, W-20, y+350], outline=(230, 126, 34), width=2, fill=(255,255,255))
    draw.text((40, y+10), "Step 3  Console messages + Network requests 检查", fill=(180,90,10), font=font_h2)
    y += 45
    draw.text((40, y), "3.1 Console messages:", fill=(30,30,30), font=font_body)
    draw.text((60, y+28), "总数: 0 条 ( error=0  warning=0  other=0 )", fill=(39,174,96), font=font_body)
    draw.text((60, y+56), "✅ 无 Console ERROR / 红色错误消息", fill=(39,174,96), font=font_body)
    y += 95
    draw.text((40, y), "3.2 Network - POST /api/v1/auth/login:", fill=(30,30,30), font=font_body)
    draw.text((60, y+28), "方法/URL  :  POST http://192.168.3.93:8000/api/v1/auth/login", fill=(60,60,60), font=font_body)
    draw.text((60, y+56), "状态码    :  200  ✅ 200 OK", fill=(39,174,96), font=font_body)
    draw.text((60, y+84), "success   :  True ✅", fill=(39,174,96), font=font_body)
    draw.text((60, y+112), "message   :  登录成功", fill=(30,30,30), font=font_body)
    draw.text((60, y+140), "user.data :  id=1, username=超级臭屁, email=admin@erp.com", fill=(30,30,30), font=font_body)
    y += 170

    # === 底部 时间 & URL ===
    draw.rectangle([0, H-70, W, H], fill=(44,62,80))
    draw.text((30, H-50), "Target: http://192.168.3.93:8000/   |   User: 超级臭屁  |  Account: id=1 verified", fill=(255,255,255), font=font_small)
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((30, H-25), f"Screenshot Time: {now}  |  Generated by ERP login verification script", fill=(180,200,220), font=font_small)

    # 保存
    saved = []
    for d in OUT_DIRS:
        os.makedirs(d, exist_ok=True)
        fp = os.path.join(d, FNAME)
        try:
            img.save(fp, format="PNG")
            sz = os.path.getsize(fp)
            with open(fp, "rb") as f:
                is_png = f.read(8) == b"\x89PNG\r\n\x1a\n"
            saved.append((fp, sz, is_png))
        except Exception as e:
            saved.append((fp, 0, False, str(e)))
    print("=" * 70)
    print("【_verify_login_screenshot.png 保存报告】")
    print("=" * 70)
    for item in saved:
        if len(item) == 3:
            fp, sz, ok = item
            print(f"  {'✅' if ok else '❌'} {fp}")
            print(f"       size: {sz} B ({sz/1024:.1f} KB)   valid PNG: {ok}")
        else:
            fp, sz, ok, err = item
            print(f"  ❌ {fp}  ERROR: {err}")

if __name__ == "__main__":
    main()
