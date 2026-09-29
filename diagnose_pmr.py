# -*- coding: utf-8 -*-
"""诊断 py_mini_racer parse 失败的具体原因"""
import sys, os, re, tempfile
sys.path.insert(0, r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\site-packages')
from py_mini_racer import MiniRacer

JS_FILE = os.path.join(tempfile.gettempdir(), 'inline_scripts.js')
with open(JS_FILE, encoding='utf-8') as f:
    js = f.read()

print(f"Total JS length: {len(js)} chars")
print(f"First 500 chars:\n{js[:500]}")
print("\n" + "="*60)

# 策略1: 只执行前 N 行，看看哪行开始炸
lines = js.splitlines()
ctx = MiniRacer()
bad_line = None
accumulated = []
for i, line in enumerate(lines[:500], 1):
    accumulated.append(line)
    chunk = "\n".join(accumulated)
    try:
        ctx2 = MiniRacer()  # 每个 chunk 用新 context 避免污染
        ctx2.execute(chunk)
        if i == 1 or i % 20 == 0:
            print(f"  前 {i} 行: PASS (chunk size={len(chunk)})")
    except Exception as e:
        estr = str(e)
        print(f"  第 {i} 行 FAIL: 错误前 {i-1} 行还 PASS")
        print(f"     当前行内容: {line[:200]!r}")
        print(f"     错误: {estr[:500]}")
        bad_line = i
        # 后退10行再试仅一行
        for j in range(max(1, i-5), i+1):
            try:
                MiniRacer().execute(lines[j-1])
                print(f"     单独第 {j} 行 PASS")
            except Exception as ee:
                print(f"     单独第 {j} 行 FAIL -> {str(ee)[:300]}")
                print(f"     内容: {lines[j-1][:200]!r}")
        break

if not bad_line:
    print(f"  前 {len(lines[:500])} 行全部 PASS")
    # 继续试更多行
    print("  整段 243K 执行:")
    try:
        MiniRacer().execute(js)
        print("     整段 PASS! SyntaxError = NO")
    except Exception as e:
        estr = str(e)
        print(f"     整段 FAIL: {estr[:800]}")
        # 二分查找坏行
        lo, hi = 1, len(lines)
        last_bad = None
        while lo < hi:
            mid = (lo + hi)//2
            chunk = "\n".join(lines[:mid])
            try:
                MiniRacer().execute(chunk)
                lo = mid + 1
            except Exception:
                hi = mid
                last_bad = mid
        print(f"  二分定位: 第 {lo} 行首次 parse 失败 (last_bad={last_bad})")
        for k in range(max(1,lo-3), min(len(lines),lo+3)+1):
            try:
                MiniRacer().execute(lines[k-1])
                print(f"    第 {k} 行单独 PASS:  {lines[k-1][:120]!r}")
            except Exception as ee:
                print(f"    第 {k} 行单独 FAIL:  {str(ee)[:200]}")
                print(f"      内容: {lines[k-1][:200]!r}")

# 检查 stub 本身
print("\n" + "="*60)
print("测试最小 stub 是否能 parse")
stub1 = "var window = {};"
stub2 = """
var window = { addEventListener: function(){}, location:{hash:'',href:''} };
var document = { getElementById:function(){return null;} };
"""
for label, code in [("stub1", stub1), ("stub2", stub2)]:
    try:
        MiniRacer().execute(code)
        print(f"  {label}: PASS")
    except Exception as e:
        print(f"  {label}: FAIL -> {str(e)[:400]}")
