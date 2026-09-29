# -*- coding: utf-8 -*-
"""解压 py_mini_racer wheel 到项目 site-packages 并测试 import"""
import zipfile, os, sys, glob

proj = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"
wheel_pattern = os.path.join(proj, "pip_dl", "py_mini_racer*.whl")
wheels = glob.glob(wheel_pattern)
print("Wheels found:", wheels)
if not wheels:
    sys.exit("No wheel")
wheel = wheels[0]
target = os.path.join(proj, "site-packages")
os.makedirs(target, exist_ok=True)

with zipfile.ZipFile(wheel, 'r') as z:
    names = z.namelist()
    print(f"Wheel 包含 {len(names)} 项；仅解压 py_mini_racer 目录和数据文件")
    for n in names:
        if n.startswith("py_mini_racer/") or n.startswith("py_mini_racer-"):
            target_path = os.path.join(target, n)
            if n.endswith("/"):
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'wb') as f:
                    f.write(z.read(n))
print("解压完成")

# 验证 import
sys.path.insert(0, target)
from py_mini_racer import MiniRacer
print("MiniRacer import OK")
ctx = MiniRacer()
res = ctx.eval("1+2")
print(f"MiniRacer eval 1+2 = {res}")

# 语法检查示例
try:
    ctx.execute("const a = 1; const b = {x: 1}; a + b.x")
    print("语法解析示例通过")
except Exception as e:
    print(f"语法解析示例失败: {e}")
