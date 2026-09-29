# -*- coding: utf-8 -*-
"""
ERP 登录全流程自动化测试
Step 2: 浏览器自动化（Playwright 模拟手机访问 + 登录）
Step 3: Console + Network 检查
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
import traceback

BASE_URL = "http://192.168.3.93:8000"
LOGIN_API = BASE_URL + "/api/v1/auth/login"
LOGIN_USER = "超级臭屁"
LOGIN_PASS = "123456"

OUT_DIRS = [
    r"C:\Users\ruancanling\Desktop",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING",
]
SCREENSHOT_NAME = "_verify_login_screenshot.png"

def print_step(num, title):
    sep = "=" * 80
    print(f"\n{sep}\nStep 2.{num}：{title}\n{sep}")


def test_homepage_http():
    """Step 2.1 辅助：先 HTTP 验证主页可达"""
    print_step(0, "(前置) HTTP 验证主页与登录 API")
    try:
        req = urllib.request.Request(BASE_URL + "/", method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            status = resp.getcode()
            has_title = "ERP智能系统" in html or "ERP系统" in html
            has_username = 'id="login-username"' in html
            has_password = 'id="login-password"' in html
            has_login_btn = 'id="login-btn"' in html
            print(f"[HTTP] GET /  Status: {status}")
            print(f"  - 含 'ERP智能系统' / 'ERP系统' 标题: {'✅' if has_title else '❌'}")
            print(f"  - 用户名输入框 (login-username):       {'✅ 存在' if has_username else '❌ 缺失'}")
            print(f"  - 密码输入框 (login-password):         {'✅ 存在' if has_password else '❌ 缺失'}")
            print(f"  - 登录按钮 (login-btn):                {'✅ 存在' if has_login_btn else '❌ 缺失'}")
            return status == 200 and has_title
    except Exception as e:
        print(f"[HTTP] GET / 失败: {e}")
        return False


def test_login_api():
    """Step 3: Network 登录 API 调用测试"""
    print_step(0, "(前置 Step 3 准备) 登录 POST /api/v1/auth/login 网络测试")
    body = json.dumps({"username": LOGIN_USER, "password": LOGIN_PASS}).encode("utf-8")
    req = urllib.request.Request(
        LOGIN_API,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = resp.getcode()
            resp_body = resp.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(resp_body)
            except Exception:
                data = {"raw": resp_body[:500]}
            success = data.get("success", False) if isinstance(data, dict) else False
            print(f"[Network] POST {LOGIN_API}")
            print(f"  - Request:  username='{LOGIN_USER}', password='{LOGIN_PASS}'")
            print(f"  - 状态码:   {status}  {'✅ 200 OK' if status == 200 else '❌ 非 200'}")
            print(f"  - success:  {success}  {'✅ True' if success else '❌ False'}")
            print(f"  - message:  {data.get('message', '') if isinstance(data, dict) else '-'}")
            if isinstance(data, dict) and data.get("data"):
                print(f"  - user:     {json.dumps(data['data'], ensure_ascii=False)}")
            print(f"  - response(raw前300字): {resp_body[:300]}")
            return {"status": status, "success": success, "response": data}
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        print(f"[Network] POST 失败，HTTP {e.code}: {e.reason}")
        print(f"  - Response: {err_body[:500]}")
        return {"status": e.code, "success": False, "response": err_body[:500]}
    except Exception as e:
        print(f"[Network] POST 异常: {e}")
        return {"status": 0, "success": False, "response": str(e)}


def run_playwright_browser_test():
    """Step 2: Playwright 浏览器自动化（模拟手机视口 + 中文输入）"""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError as e:
        print(f"\n[Playwright] 未安装，跳过浏览器自动化部分: {e}")
        return False

    console_log = []
    network_log = []

    print_step(1, f"导航到 {BASE_URL}/  (模拟手机 390×844 视口)")
    with sync_playwright() as p:
        # 启动 Chromium，手机 UA + 视口
        iphone = p.devices["iPhone 12 Pro"]
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**iphone, locale="zh-CN")
        context.set_default_timeout(15000)

        page = context.new_page()

        # 捕获 console 消息
        def on_console(msg):
            console_log.append({
                "type": msg.type,          # log / warning / error / ...
                "text": msg.text[:500],
                "args_count": len(msg.args),
            })
        page.on("console", on_console)

        # 捕获网络请求（关注登录 POST）
        def on_response(resp):
            url = resp.url
            if "/api/v1/auth/login" in url:
                try:
                    body_txt = resp.text()
                except Exception:
                    body_txt = ""
                network_log.append({
                    "url": url,
                    "status": resp.status,
                    "ok": resp.ok,
                    "method": resp.request.method,
                    "response_body_preview": body_txt[:500],
                })
            elif "/api/v1/" in url or url.endswith((".js", ".css", ".png", ".html")):
                if resp.status >= 400:
                    network_log.append({
                        "url": url[:120],
                        "status": resp.status,
                        "ok": resp.ok,
                        "method": resp.request.method,
                        "warning": "status >= 400",
                    })
        page.on("response", on_response)

        # --- 2.1 导航 ---
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        time.sleep(2)

        # --- 2.2 snapshot 确认登录页元素 ---
        print_step(2, "等待 2s，snapshot 确认登录页元素")
        content = page.content()
        title = page.title()
        has_t = "ERP智能系统" in title or "ERP系统" in title or "ERP智能系统" in content
        has_u = "login-username" in content
        has_p = "login-password" in content
        has_b = "login-btn" in content
        # 尝试找元素（更精确）
        found_el = {}
        for sel, name in [("#login-username", "用户名输入框"),
                          ("#login-password", "密码输入框"),
                          ("#login-btn",      "登录按钮")]:
            try:
                el = page.query_selector(sel)
                found_el[name] = {
                    "found": el is not None,
                    "tag": el.evaluate("e => e.tagName") if el else None,
                    "type_attr": el.evaluate("e => e.getAttribute('type')") if el else None,
                    "id_attr": el.evaluate("e => e.id") if el else None,
                    "text": (el.evaluate("e => e.textContent") or "")[:30] if el else None,
                }
            except Exception as e2:
                found_el[name] = {"found": False, "error": str(e2)}

        print(f"  - Page Title: {title}")
        print(f"  - 页面包含 'ERP智能系统/登录' 字样: {'✅' if has_t else '❌'}")
        print(f"  - 用户名输入框#login-username HTML存在: {'✅' if has_u else '❌'}")
        print(f"  - 密码输入框#login-password HTML存在:   {'✅' if has_p else '❌'}")
        print(f"  - 登录按钮#login-btn HTML存在:          {'✅' if has_b else '❌'}")
        print(f"  - 元素精确提取 (querySelector + evaluate):")
        for n, info in found_el.items():
            if info.get("found"):
                print(f"      ✅ {n}: tag={info['tag']}, id={info['id_attr']}, type={info['type_attr']}, text={info['text']!r}")
            else:
                print(f"      ❌ {n}: {info}")

        # --- 2.3 提取 ref 结果（上面就是基于 selector 的提取，这里汇总） ---
        print_step(3, "snapshot 提取输入框 / 按钮 ref 信息")
        # Playwright 用 selector 而非 ref。这里输出 selector 等价映射：
        print(f"  [用户名输入框 ref 等价]  selector: #login-username  ->  found: {found_el.get('用户名输入框', {}).get('found')}")
        print(f"  [密码输入框   ref 等价]  selector: #login-password  ->  found: {found_el.get('密码输入框', {}).get('found')}")
        print(f"  [登录按钮     ref 等价]  selector: #login-btn       ->  found: {found_el.get('登录按钮', {}).get('found')}")

        # --- 2.4 输入用户名 ---
        print_step(4, f"输入用户名：{LOGIN_USER!r}")
        try:
            username_el = page.query_selector("#login-username")
            username_el.click()
            username_el.fill("")
            username_el.type(LOGIN_USER, delay=50)
            actual_val = username_el.evaluate("e => e.value")
            print(f"  - 实际输入框值: {actual_val!r}")
            print(f"  - 结果: {'✅ 一致' if actual_val == LOGIN_USER else '❌ 不一致'}")
        except Exception as e:
            print(f"  - ❌ 输入用户名失败: {e}")

        # --- 2.5 输入密码 + Enter 提交 ---
        print_step(5, f"输入密码：{LOGIN_PASS!r}，按 Enter 登录")
        try:
            pwd_el = page.query_selector("#login-password")
            pwd_el.click()
            pwd_el.fill("")
            pwd_el.type(LOGIN_PASS, delay=50)
            actual_pwd = pwd_el.evaluate("e => e.value")
            print(f"  - 实际密码框值: {'*' * len(actual_pwd)} ({len(actual_pwd)} chars)")
            print(f"  - 结果: {'✅ 一致' if actual_pwd == LOGIN_PASS else '❌ 不一致'}")
            # 按 Enter
            pwd_el.press("Enter")
            print(f"  - 已按 Enter 提交登录表单")
        except Exception as e:
            print(f"  - ❌ 输入密码/提交失败: {e}")

        # --- 2.6 等待 3s，snapshot 确认进入主 App ---
        print_step(6, "等待 3s，snapshot 确认进入主 App")
        time.sleep(3)

        try:
            # 等 main-app 可见
            main_app = page.query_selector("#main-app")
            login_page = page.query_selector("#login-page")
            main_display = main_app.evaluate("e => window.getComputedStyle(e).display") if main_app else None
            login_display = login_page.evaluate("e => window.getComputedStyle(e).display") if login_page else None
            user_name_el = page.query_selector("#current-user-name")
            current_user_text = user_name_el.evaluate("e => e.textContent") if user_name_el else ""

            sidebar_exists = page.query_selector(".sidebar-menu") is not None
            content_exists = page.query_selector("#content") is not None
            # 检查欢迎/仪表盘等文字
            content_html = page.query_selector("#content").inner_html() if content_exists else ""
            has_dashboard_keyword = any(k in content_html for k in ["欢迎", "仪表盘", "系统", "物料总数", "dashboard"])

            print(f"  - login-page display:  {login_display!r}  {'✅ 已隐藏' if login_display == 'none' else '❌ 未隐藏'}")
            print(f"  - main-app   display:  {main_display!r}  {'✅ 已显示' if main_display and main_display != 'none' else '❌ 未显示'}")
            print(f"  - 左侧菜单 .sidebar-menu: {'✅ 存在' if sidebar_exists else '❌ 不存在'}")
            print(f"  - 内容区 #content:        {'✅ 存在' if content_exists else '❌ 不存在'}")
            print(f"  - #current-user-name:   '{current_user_text}'  {'✅ 显示用户名' if LOGIN_USER in current_user_text or current_user_text else '❌ 未显示'}")
            print(f"  - 内容区含 欢迎/仪表盘/系统 等关键字: {'✅' if has_dashboard_keyword else '❌'}")

            if main_display and main_display != "none":
                print("  ✅ 判定：已成功进入主 App")
            else:
                # 额外检查消息区是否有错误
                msg_el = page.query_selector("#login-message")
                msg_txt = msg_el.inner_text() if msg_el else "(no login-message el)"
                print(f"  ⚠️  登录消息区: {msg_txt[:200]}")
        except Exception as e:
            print(f"  - ❌ snapshot 主App异常: {e}\n{traceback.format_exc()}")

        # --- 2.7 点击左侧"物料管理" tab，snapshot 确认物料页面渲染 ---
        print_step(7, "点击左侧 '物料管理' tab，snapshot 确认物料页面")
        try:
            # 找物料管理按钮（onclick=loadModule('materials') 或 textContent包含 物料管理）
            mat_btn = None
            candidates = page.query_selector_all(".sidebar-menu button")
            for b in candidates:
                txt = b.evaluate("e => e.textContent") or ""
                onclick = b.evaluate("e => e.getAttribute('onclick')") or ""
                if "物料管理" in txt or "materials" in onclick:
                    mat_btn = b
                    break
            if mat_btn is None:
                # 用 onclick 再试
                mat_btn = page.query_selector("button[onclick*=\"'materials'\"]") or page.query_selector("button[onclick*='\"materials\"']")

            if mat_btn:
                txt = mat_btn.evaluate("e => e.textContent")
                print(f"  - 找到物料管理按钮: {txt!r}，点击中...")
                mat_btn.click()
                time.sleep(2)
                content_after = page.query_selector("#content")
                html_after = content_after.inner_html() if content_after else ""
                has_materials_key = any(k in html_after for k in ["物料", "库存", "materials", "物料总数", "规格型号"])
                print(f"  - 点击后内容区包含 物料/库存/materials 关键字: {'✅' if has_materials_key else '❌'}")
                if has_materials_key:
                    # 取前200字HTML预览
                    preview = html_after.replace("\n", " ")[:300]
                    print(f"  - 内容区HTML预览(300字): {preview}")
            else:
                print("  - ❌ 未找到 '物料管理' 按钮")
        except Exception as e:
            print(f"  - ❌ 物料管理tab点击异常: {e}\n{traceback.format_exc()}")

        # --- 2.8 全屏截图保存 ---
        print_step(8, "截取全屏图，保存为 _verify_login_screenshot.png")
        saved_paths = []
        try:
            screenshot_bytes = page.screenshot(full_page=True, type="png")
            for d in OUT_DIRS:
                os.makedirs(d, exist_ok=True)
                fp = os.path.join(d, SCREENSHOT_NAME)
                with open(fp, "wb") as f:
                    f.write(screenshot_bytes)
                sz = os.path.getsize(fp)
                saved_paths.append((fp, sz))
                print(f"  ✅ 保存: {fp}  ({sz} B / {sz/1024:.1f} KB)")
        except Exception as e:
            print(f"  ❌ 截图失败: {e}")

        browser.close()

        # --- Step 3: Console / Network 报告 ---
        print("\n" + "=" * 80)
        print("【Step 3：浏览器 Console / Network 检查报告】")
        print("=" * 80)

        print("\n[3.1] Console messages:")
        errors = [c for c in console_log if c["type"] in ("error",)]
        warnings = [c for c in console_log if c["type"] == "warning"]
        others = [c for c in console_log if c["type"] not in ("error", "warning")]
        print(f"  - 总数: {len(console_log)} 条 (error={len(errors)}, warning={len(warnings)}, other={len(others)})")
        if errors:
            print("  ❌ 发现 错误(ERROR/RED) 消息：")
            for i, c in enumerate(errors, 1):
                print(f"    [{i}] [{c['type'].upper()}] {c['text'][:400]}")
        else:
            print("  ✅ 无 Console ERROR / 红色错误消息")
        if warnings:
            print("  ⚠️  Warning 消息 (首5条):")
            for i, c in enumerate(warnings[:5], 1):
                print(f"    [{i}] [WARN] {c['text'][:300]}")
        if others:
            print(f"  ℹ️  普通 console.log/info 共 {len(others)} 条 (首3条示例):")
            for i, c in enumerate(others[:3], 1):
                print(f"    [{i}] [{c['type']}] {c['text'][:200]}")

        print("\n[3.2] Network requests (关注登录 /api/v1/auth/login):")
        login_req = [n for n in network_log if "/api/v1/auth/login" in n.get("url", "")]
        if login_req:
            for i, n in enumerate(login_req, 1):
                print(f"  [{i}] {n.get('method')} {n.get('url')}")
                print(f"      状态码: {n.get('status')}  {'✅ 200' if n.get('status') == 200 else '❌ !=200'}")
                print(f"      ok:     {n.get('ok')}")
                # 解析 body 中 success
                body = n.get("response_body_preview", "")
                try:
                    data = json.loads(body) if body else {}
                    print(f"      success: {data.get('success')}  {'✅ True' if data.get('success') else '❌ False/Null'}")
                    print(f"      message: {data.get('message', '')}")
                    print(f"      data.user: {json.dumps(data.get('data', {}), ensure_ascii=False)[:200]}")
                except Exception:
                    print(f"      response-body: {body[:300]}")
        else:
            print("  ⚠️  未捕获到 /api/v1/auth/login 网络请求（可能已由页面 fetch 发出但 response 事件略过）")

        # 其他网络错误
        bad_reqs = [n for n in network_log if n.get("warning") or (n.get("status") and n.get("status", 0) >= 400)]
        if bad_reqs:
            print(f"\n  ⚠️  其他 >=400 网络请求 ({len(bad_reqs)} 条，首5条):")
            for i, n in enumerate(bad_reqs[:5], 1):
                print(f"    [{i}] {n.get('method')} {n.get('status')} {n.get('url')}")
        else:
            print("\n  ✅ 其他接口/静态资源无 >=400 的异常请求")

    return True


def main():
    print("\n" + "=" * 80)
    print(" ERP 登录自动化 + 网络控制台 测试程序")
    print(" 目标URL : " + BASE_URL)
    print(" 账号    : " + LOGIN_USER + " / " + LOGIN_PASS)
    print("=" * 80)

    # Step 2.0 / Step 3 先 HTTP 层面测通
    ok_home = test_homepage_http()
    login_api_result = test_login_api()

    # Step 2 Playwright 浏览器自动化 + Step 3 console/network
    pw_ok = run_playwright_browser_test()

    # ====== 最终总结 ======
    print("\n" + "#" * 80)
    print(" 【最终总结】")
    print("#" * 80)
    print(f"  HTTP 主页可达:            {'✅ 是' if ok_home else '❌ 否'}")
    print(f"  登录API status==200:      {'✅ 是' if login_api_result.get('status') == 200 else '❌ 否 (status=' + str(login_api_result.get('status')) + ')'}")
    print(f"  登录API success==True:    {'✅ 是' if login_api_result.get('success') else '❌ 否'}")
    print(f"  Playwright 浏览器测试:    {'✅ 执行完毕' if pw_ok else '❌ 未执行(见上)'}")
    print("  截图文件:")
    for d in OUT_DIRS:
        fp = os.path.join(d, SCREENSHOT_NAME)
        if os.path.exists(fp):
            print(f"    - {fp}  [{os.path.getsize(fp)} B, 合法PNG: {check_png(fp)}]")
        else:
            print(f"    - {fp}  ❌ 不存在")
    print("#" * 80)


def check_png(fp):
    try:
        with open(fp, "rb") as f:
            sig = f.read(8)
        return sig == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


if __name__ == "__main__":
    main()
