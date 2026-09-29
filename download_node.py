# -*- coding: utf-8 -*-
"""下载便携版 node.exe 到项目目录 tools/ 下"""
import urllib.request
import zipfile
import os, sys, io

URL = "https://nodejs.org/dist/v20.17.0/node-v20.17.0-win-x64.zip"
proj = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"
dest_dir = os.path.join(proj, "tools")
os.makedirs(dest_dir, exist_ok=True)
zip_path = os.path.join(dest_dir, "node-v20.17.0-win-x64.zip")
node_exe = os.path.join(dest_dir, "node.exe")

if not os.path.exists(node_exe):
    if not os.path.exists(zip_path):
        print(f"下载 {URL} ...")
        def hook(count, block, total):
            if count % 200 == 0 or total > 0 and count*block >= total:
                pct = count*block*100/max(1,total)
                print(f"  {count*block/1024/1024:.1f}MB / {total/1024/1024:.1f}MB ({pct:.1f}%)")
        urllib.request.urlretrieve(URL, zip_path, hook if False else None)  # hook disabled for stability
        print(f"下载完成: {os.path.getsize(zip_path)} bytes")
    print(f"解压 {zip_path} ...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        for n in z.namelist():
            if n.endswith('/node.exe'):
                print(f"  提取 {n} -> tools/node.exe")
                with open(node_exe, 'wb') as f:
                    f.write(z.read(n))
                break
        else:
            print("  ERROR: zip 里没找到 node.exe")
            sys.exit(1)
print(f"OK: {node_exe} 存在, 大小={os.path.getsize(node_exe)} bytes")

# 测试 node
import subprocess
r = subprocess.run([node_exe, '--version', '--check' if False else ''], capture_output=True, text=True, timeout=20)
print(f"node --version: rc={r.returncode}  out={r.stdout.strip()}  err={r.stderr.strip()[:200]}")

# 真实 node --version
r2 = subprocess.run([node_exe, '-e', 'console.log(process.version)'], capture_output=True, text=True, timeout=20)
print(f"node eval version: {r2.stdout.strip()} (rc={r2.returncode}, err={r2.stderr.strip()[:100]})")

# 语法检查 inline_scripts.js
import tempfile
js_path = os.path.join(tempfile.gettempdir(), 'inline_scripts.js')
if os.path.exists(js_path):
    print(f"\n对 {js_path} ({os.path.getsize(js_path)} bytes) 执行 node --check ...")
    r3 = subprocess.run([node_exe, '--check', js_path], capture_output=True, text=True, timeout=30)
    print(f"  rc={r3.returncode}")
    if r3.returncode == 0:
        print("  PASS: SyntaxError = NO")
    else:
        print("  FAIL: SyntaxError = YES")
        print("  STDERR:")
        for ln in r3.stderr.splitlines()[:25]: print("   >", ln)
else:
    print(f"\n[WARN] {js_path} 不存在，跳过语法检查")
