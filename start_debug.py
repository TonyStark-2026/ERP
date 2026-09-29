import subprocess
import time
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting uvicorn server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "debug"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(5)

return_code = proc.poll()
if return_code is not None:
    stdout, stderr = proc.communicate()
    print(f"Server exited with code: {return_code}")
    print("STDOUT:")
    print(stdout)
    print("\nSTDERR:")
    print(stderr)
else:
    print("Server is running...")
    print("Trying to access health endpoint...")
    
    try:
        import urllib.request
        response = urllib.request.urlopen("http://localhost:8080/health", timeout=5)
        print(f"Health check passed: {response.read().decode()}")
        print("Server started successfully!")
        
        while True:
            line = proc.stdout.readline()
            if line:
                print(line.strip())
            else:
                break
    except Exception as e:
        print(f"Health check failed: {e}")
        stdout, stderr = proc.communicate()
        print("STDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)