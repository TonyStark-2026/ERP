# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\site-packages')
print("sys.path 0:", sys.path[0])
print()
# 逐个测试
from py_mini_racer.py_mini_racer import LibLocation, dll
print("dll path:", LibLocation())
print("dll object:", dll)
print()
# 用 ctx 最简单数字计算
from py_mini_racer import MiniRacer
cases = [
    ("2+2", lambda c: c.eval("2+2")),
    ("empty exec", lambda c: c.execute("")),
    ("empty comment", lambda c: c.execute("// a comment")),
    ("var x=1", lambda c: c.execute("var x=1;")),
    ("var x=1 then eval", lambda c: (c.execute("var x=42;"), c.eval("x"))[1]),
]
for label, fn in cases:
    try:
        ctx = MiniRacer()
        r = fn(ctx)
        print(f"  PASS {label}: {r}")
    except Exception as e:
        print(f"  FAIL {label}: {e}")
