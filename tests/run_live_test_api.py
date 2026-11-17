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

# Wait for server to be responsive
url = "http://127.0.0.1:5000/api/health/db"
started = False
for _ in range(30):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            started = True
            print("Flask server is up and responsive on http://127.0.0.1:5000!")
            break
    except Exception:
        time.sleep(1)

if not started:
    print("Failed to start Flask server in time.")
    server_process.terminate()
    sys.exit(1)

try:
    print("\nRunning official test_api.py...")
    test_proc = subprocess.run(
        [python_exe, "test_api.py"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True
    )
    print("test_api.py STDOUT:")
    print(test_proc.stdout)
    if test_proc.stderr:
        print("test_api.py STDERR:")
        print(test_proc.stderr)
finally:
    print("Terminating Flask server...")
    server_process.terminate()
    server_process.wait()

# Read test_report.txt
report_path = ROOT_DIR / "test_report.txt"
if report_path.exists():
    print("\n=== Contents of test_report.txt ===")
    print(report_path.read_text(encoding="utf-8"))
