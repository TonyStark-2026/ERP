# -*- coding: utf-8 -*-
"""
凭证中心 (Voucher Center) 自动化测试脚本
测试功能点：
1. 统计卡片 (草稿/待审核/已审核/已过账/已驳回/本月凭证)
2. 待审核凭证 tab 列表
3. 点击 👁 查看凭证详情
4. 规则配置 tab
5. 异常预警 tab
6. 汇总查询 tab
"""
import os
import sys
import time
import json
import traceback

BASE_URL = "http://127.0.0.1:8000"
LOGIN_USER = "超级臭屁"
LOGIN_PASS = "123456"
SCREENSHOT_DIR = r"C:\Users\ruancanling\Desktop\ERP VIBE CODING\screenshots"

def ensure_dir():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_screenshot(page, name):
    ensure_dir()
    path = os.path.join(SCREENSHOT_DIR, name)
    page.screenshot(path=path, full_page=True)
    print(f"  📸 截图已保存: {path}")
    return path

def log_step(step_num, title):
    sep = "=" * 60
    print(f"\n{sep}\nStep {step_num}: {title}\n{sep}")

def main():
    from playwright.sync_api import sync_playwright

    results = {
        "stats_cards": {"status": "unknown", "detail": ""},
        "pending_tab": {"status": "unknown", "detail": ""},
        "view_detail": {"status": "unknown", "detail": ""},
        "templates_tab": {"status": "unknown", "detail": ""},
        "exceptions_tab": {"status": "unknown", "detail": ""},
        "query_tab": {"status": "unknown", "detail": ""},
    }

    console_errors = []
    network_errors = []

    with sync_playwright() as p:
        print("🚀 启动 Chromium 浏览器...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900}, locale="zh-CN")
        page = context.new_page()

        # 捕获 console 错误
        page.on("console", lambda msg: (
            console_errors.append({"type": msg.type, "text": msg.text[:300]})
            if msg.type in ("error", "warning") else None
        ))

        # 捕获网络错误
        page.on("response", lambda resp: (
            network_errors.append({"url": resp.url[:120], "status": resp.status})
            if resp.status >= 400 and "/api/" in resp.url else None
        ))

        # ========== Step 0: 导航到主页 ==========
        log_step(0, "导航到主页")
        page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        time.sleep(2)
        take_screenshot(page, "00_homepage.png")
        print(f"  当前页面标题: {page.title()}")
        print(f"  当前URL: {page.url}")

        # ========== Step 1: 登录 ==========
        log_step(1, "登录系统")
        content = page.content()

        if "login-username" in content or "login-password" in content:
            print("  检测到登录页面，开始登录...")
            page.fill("#login-username", LOGIN_USER)
            page.fill("#login-password", LOGIN_PASS)
            take_screenshot(page, "01_login_page.png")
            page.click("#login-btn")
            time.sleep(3)
            take_screenshot(page, "02_after_login.png")
            print(f"  登录后URL: {page.url}")
        elif "main-app" in content:
            print("  已登录状态，直接进入系统")
        else:
            print(f"  ⚠️ 未知页面状态，尝试继续...")
            take_screenshot(page, "01_unknown_state.png")

        # ========== Step 2: 导航到凭证中心 ==========
        log_step(2, "点击侧边栏 '📝 凭证中心'")

        # 尝试找到凭证中心按钮
        voucher_btn = None
        try:
            # 方式1: 通过文本查找
            elements = page.query_selector_all(".sidebar-menu button, .sidebar-menu li button")
            for el in elements:
                text = el.inner_text()
                if "凭证中心" in text or "voucher" in text.lower():
                    voucher_btn = el
                    print(f"  找到凭证中心按钮: '{text.strip()}'")
                    break

            # 方式2: 通过 data-module 属性
            if not voucher_btn:
                voucher_btn = page.query_selector('button[data-module="voucher"], li[data-module="voucher"] button')
                if voucher_btn:
                    print("  通过 data-module 属性找到按钮")

            # 方式3: 通过 onclick 属性
            if not voucher_btn:
                voucher_btn = page.query_selector('button[onclick*="loadModule(\'voucher\')"], button[onclick*="loadModule(\"voucher\")"]')
                if voucher_btn:
                    print("  通过 onclick 属性找到按钮")

            if voucher_btn:
                voucher_btn.click()
                print("  ✅ 已点击凭证中心按钮")
                time.sleep(2)
                take_screenshot(page, "03_voucher_center_main.png")
            else:
                print("  ❌ 未找到凭证中心按钮，尝试通过 JS 直接加载...")
                page.evaluate("loadModule('voucher')")
                time.sleep(2)
                take_screenshot(page, "03_voucher_center_main.png")

        except Exception as e:
            print(f"  ❌ 点击凭证中心异常: {e}")
            # 降级方案
            page.evaluate("if(typeof loadModule==='function')loadModule('voucher')")
            time.sleep(2)
            take_screenshot(page, "03_voucher_center_main.png")

        # ========== Step 3: 统计卡片测试 ==========
        log_step(3, "测试统计卡片")
        try:
            stats_el = page.query_selector("#voucher-stats")
            if stats_el:
                stats_html = stats_el.inner_html()
                # 检查是否包含6个统计卡片
                cards = stats_el.query_selector_all("> div")
                print(f"  统计卡片数量: {len(cards)}")

                card_texts = []
                for i, card in enumerate(cards):
                    text = card.inner_text().strip()
                    card_texts.append(text)
                    print(f"  卡片{i+1}: {text[:80]}")

                # 检查关键字段
                has_draft = any("草稿" in t or "draft" in t.lower() for t in card_texts)
                has_pending = any("待审核" in t or "pending" in t.lower() for t in card_texts)
                has_approved = any("已审核" in t or "approved" in t.lower() for t in card_texts)
                has_posted = any("已过账" in t or "posted" in t.lower() for t in card_texts)
                has_rejected = any("已驳回" in t or "rejected" in t.lower() for t in card_texts)
                has_month = any("本月" in t or "month" in t.lower() for t in card_texts)

                checks = {
                    "📝 草稿": has_draft,
                    "⏳ 待审核": has_pending,
                    "✅ 已审核": has_approved,
                    "📤 已过账": has_posted,
                    "❌ 已驳回": has_rejected,
                    "📅 本月凭证": has_month,
                }

                for name, ok in checks.items():
                    print(f"    {name}: {'✅' if ok else '❌'}")

                all_ok = all(checks.values())
                results["stats_cards"]["status"] = "pass" if all_ok else "fail"
                results["stats_cards"]["detail"] = f"6个卡片: {len(cards)}个; 字段检查: {sum(checks.values())}/6通过"
            else:
                print("  ❌ 未找到 #voucher-stats 元素")
                results["stats_cards"]["status"] = "fail"
                results["stats_cards"]["detail"] = "未找到统计卡片元素"
        except Exception as e:
            print(f"  ❌ 统计卡片测试异常: {e}")
            results["stats_cards"]["status"] = "error"
            results["stats_cards"]["detail"] = str(e)[:200]

        # ========== Step 4: 待审核凭证 Tab 测试 ==========
        log_step(4, "测试待审核凭证 Tab")
        try:
            # 确保在 pending tab
            page.evaluate("switchVoucherTab('pending')")
            time.sleep(1)

            # 检查凭证列表
            list_el = page.query_selector("#voucher-list")
            if list_el:
                list_html = list_el.inner_html()
                has_data = "暂无凭证" not in list_html and list_html.strip() != ""
                rows = list_el.query_selector_all(".voucher-row")
                # 减去标题行
                data_rows = [r for r in rows if "凭证号" not in r.inner_text()]

                print(f"  数据行数: {len(data_rows)}")

                if data_rows:
                    # 检查第一条凭证
                    first_voucher = data_rows[0].inner_text()[:200]
                    print(f"  第一条凭证预览: {first_voucher}")

                    # 检查是否有 👁 按钮
                    view_btns = list_el.query_selector_all("button[onclick*='viewVoucher']")
                    print(f"  👁 查看按钮数量: {len(view_btns)}")

                    results["pending_tab"]["status"] = "pass"
                    results["pending_tab"]["detail"] = f"列表显示 {len(data_rows)} 条凭证"
                else:
                    results["pending_tab"]["status"] = "pass"  # 空列表也是正常的
                    results["pending_tab"]["detail"] = "列表为空（显示'暂无凭证'或无数据行）"

                take_screenshot(page, "04_pending_tab.png")
            else:
                print("  ❌ 未找到 #voucher-list 元素")
                results["pending_tab"]["status"] = "fail"
                results["pending_tab"]["detail"] = "未找到凭证列表元素"
        except Exception as e:
            print(f"  ❌ 待审核凭证 Tab 测试异常: {e}")
            results["pending_tab"]["status"] = "error"
            results["pending_tab"]["detail"] = str(e)[:200]

        # ========== Step 5: 点击 👁 查看凭证详情 ==========
        log_step(5, "点击 👁 查看凭证详情")
        try:
            view_btns = page.query_selector_all("button[onclick*='viewVoucher']")
            if view_btns:
                print(f"  找到 {len(view_btns)} 个查看按钮，点击第一个...")
                view_btns[0].click()
                time.sleep(1)

                # 检查 modal 是否显示
                modal = page.query_selector("#voucher-modal")
                if modal:
                    modal_html = modal.inner_html()
                    has_detail = "凭证详情" in modal_html
                    has_entries = "科目" in modal_html or "借方" in modal_html or "贷方" in modal_html
                    has_total = "合计" in modal_html

                    print(f"  Modal显示: ✅")
                    print(f"  包含'凭证详情': {'✅' if has_detail else '❌'}")
                    print(f"  包含分录条目: {'✅' if has_entries else '❌'}")
                    print(f"  包含合计: {'✅' if has_total else '❌'}")

                    results["view_detail"]["status"] = "pass" if (has_detail and has_entries) else "partial"
                    results["view_detail"]["detail"] = f"Modal: 详情={has_detail}, 条目={has_entries}, 合计={has_total}"

                    take_screenshot(page, "05_voucher_detail_modal.png")

                    # 关闭 modal
                    close_btn = modal.query_selector("button")
                    if close_btn:
                        close_btn.click()
                    else:
                        page.keyboard.press("Escape")
                    time.sleep(0.5)
                else:
                    print("  ❌ 未找到 #voucher-modal")
                    results["view_detail"]["status"] = "fail"
                    results["view_detail"]["detail"] = "Modal未弹出"
            else:
                print("  ⚠️ 没有可查看的凭证 (无 👁 按钮)")
                results["view_detail"]["status"] = "skip"
                results["view_detail"]["detail"] = "列表为空，无查看按钮"
        except Exception as e:
            print(f"  ❌ 查看详情异常: {e}")
            results["view_detail"]["status"] = "error"
            results["view_detail"]["detail"] = str(e)[:200]

        # ========== Step 6: 规则配置 Tab ==========
        log_step(6, "切换到规则配置 Tab")
        try:
            page.evaluate("switchVoucherTab('templates')")
            time.sleep(1.5)

            templates_el = page.query_selector("#voucher-templates")
            if templates_el:
                tpl_html = templates_el.inner_html()
                has_content = "加载中" not in tpl_html and tpl_html.strip() != ""
                template_cards = templates_el.query_selector_all("div[style*='border:1px solid']")

                print(f"  规则配置内容长度: {len(tpl_html)}")
                print(f"  找到模板卡片数: {len(template_cards)}")

                # 检查是否包含模板相关内容
                has_template = "template_name" in tpl_html or "模板" in tpl_html or "规则" in tpl_html
                print(f"  包含模板/规则内容: {'✅' if has_template else '❌'}")

                results["templates_tab"]["status"] = "pass" if has_content else "empty"
                results["templates_tab"]["detail"] = f"模板卡片: {len(template_cards)}"

                take_screenshot(page, "06_templates_tab.png")
            else:
                print("  ❌ 未找到 #voucher-templates")
                results["templates_tab"]["status"] = "fail"
                results["templates_tab"]["detail"] = "未找到规则配置元素"
        except Exception as e:
            print(f"  ❌ 规则配置 Tab 测试异常: {e}")
            results["templates_tab"]["status"] = "error"
            results["templates_tab"]["detail"] = str(e)[:200]

        # ========== Step 7: 异常预警 Tab ==========
        log_step(7, "切换到异常预警 Tab")
        try:
            page.evaluate("switchVoucherTab('exceptions')")
            time.sleep(1.5)

            exc_el = page.query_selector("#voucher-exceptions")
            if exc_el:
                exc_html = exc_el.inner_html()
                has_content = "加载中" not in exc_html and exc_html.strip() != ""
                has_no_exc = "暂无异常" in exc_html or "✅" in exc_html
                exc_cards = exc_el.query_selector_all("div[style*='border:1px solid #fee2e2']")

                print(f"  异常预警内容长度: {len(exc_html)}")
                print(f"  异常凭证卡片数: {len(exc_cards)}")
                print(f"  显示'暂无异常': {'✅' if has_no_exc and not exc_cards else '⚠️'}")

                results["exceptions_tab"]["status"] = "pass" if has_content else "empty"
                results["exceptions_tab"]["detail"] = f"异常凭证: {len(exc_cards)}张"

                take_screenshot(page, "07_exceptions_tab.png")
            else:
                print("  ❌ 未找到 #voucher-exceptions")
                results["exceptions_tab"]["status"] = "fail"
                results["exceptions_tab"]["detail"] = "未找到异常预警元素"
        except Exception as e:
            print(f"  ❌ 异常预警 Tab 测试异常: {e}")
            results["exceptions_tab"]["status"] = "error"
            results["exceptions_tab"]["detail"] = str(e)[:200]

        # ========== Step 8: 汇总查询 Tab ==========
        log_step(8, "切换到汇总查询 Tab")
        try:
            page.evaluate("switchVoucherTab('query')")
            time.sleep(1.5)

            query_el = page.query_selector("#voucher-query")
            if query_el:
                query_html = query_el.inner_html()
                has_content = "加载中" not in query_html and query_html.strip() != ""
                has_search = "q-keyword" in query_html or "关键词" in query_html
                has_status_filter = "q-status" in query_html or "状态" in query_html
                has_date_filter = "q-start" in query_html or "日期" in query_html

                print(f"  汇总查询内容长度: {len(query_html)}")
                print(f"  包含关键词搜索: {'✅' if has_search else '❌'}")
                print(f"  包含状态筛选: {'✅' if has_status_filter else '❌'}")
                print(f"  包含日期筛选: {'✅' if has_date_filter else '❌'}")

                all_ok = has_search and has_status_filter and has_date_filter
                results["query_tab"]["status"] = "pass" if all_ok else "partial"
                results["query_tab"]["detail"] = f"搜索={has_search}, 状态={has_status_filter}, 日期={has_date_filter}"

                take_screenshot(page, "08_query_tab.png")
            else:
                print("  ❌ 未找到 #voucher-query")
                results["query_tab"]["status"] = "fail"
                results["query_tab"]["detail"] = "未找到汇总查询元素"
        except Exception as e:
            print(f"  ❌ 汇总查询 Tab 测试异常: {e}")
            results["query_tab"]["status"] = "error"
            results["query_tab"]["detail"] = str(e)[:200]

        # ========== 最终截图 ==========
        log_step(9, "最终状态截图")
        take_screenshot(page, "09_final_state.png")

        # 关闭浏览器
        browser.close()

        # ========== 输出测试报告 ==========
        print("\n" + "=" * 60)
        print("📊 凭证中心测试报告")
        print("=" * 60)

        status_icons = {"pass": "✅", "partial": "⚠️", "fail": "❌", "error": "🛑", "skip": "⏭️", "empty": "📭", "unknown": "❓"}

        for name, result in results.items():
            icon = status_icons.get(result["status"], "❓")
            print(f"  {icon} {name}: {result['status']} - {result['detail']}")

        # Console 错误
        print("\n📋 Console 错误日志:")
        if console_errors:
            for err in console_errors[:10]:
                print(f"  [{err['type'].upper()}] {err['text'][:150]}")
        else:
            print("  ✅ 无 Console 错误")

        # 网络错误
        print("\n🌐 网络错误日志:")
        if network_errors:
            for err in network_errors[:10]:
                print(f"  [HTTP {err['status']}] {err['url']}")
        else:
            print("  ✅ 无 API 错误 (>=400)")

        # 截图列表
        print("\n📸 截图文件列表:")
        if os.path.exists(SCREENSHOT_DIR):
            for f in sorted(os.listdir(SCREENSHOT_DIR)):
                if f.endswith(".png"):
                    fp = os.path.join(SCREENSHOT_DIR, f)
                    sz = os.path.getsize(fp)
                    print(f"  {f} ({sz} B)")

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

if __name__ == "__main__":
    main()