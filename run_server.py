import subprocess
import time
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

time.sleep(3)

import urllib.request
try:
    urllib.request.urlopen("http://localhost:8080/health", timeout=5)
    print("SERVER STARTED SUCCESSFULLY")
except Exception as e:
    print(f"STARTUP FAILED: {e}")
    lines = proc.stdout.readlines()
    for line in lines:
        print(line.strip())
    proc.kill()
    sys.exit(1)

while True:
    try:
        line = proc.stdout.readline()
        if line:
            print(line.strip())
        else:
            break
    except:
        break
