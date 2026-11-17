import subprocess
import time
import sys
import os
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
python_exe = sys.executable

print("Starting Flask server...")
server_process = subprocess.Popen(
    [python_exe, "run.py"],
    cwd=str(ROOT_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

url = "http://127.0.0.1:5000/api/health/db"
started = False
for i in range(30):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            started = True
            print("Flask server and MongoDB Atlas connection ready!")
            break
    except Exception:
        pass
    time.sleep(1)

if not started:
    print("Failed to start Flask server in time.")
    server_process.terminate()
    sys.exit(1)

try:
    print("\nRunning standalone image OCR test...")
    test_proc = subprocess.run(
        [python_exe, "tests/test_image_ocr.py"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True
    )
    print("STDOUT:")
    print(test_proc.stdout)
    if test_proc.stderr:
        print("STDERR:")
        print(test_proc.stderr)
    if test_proc.returncode != 0:
        sys.exit(test_proc.returncode)
finally:
    server_process.terminate()
    server_process.wait()
    print("Server stopped.")
