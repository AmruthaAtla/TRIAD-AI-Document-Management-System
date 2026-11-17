import subprocess
import time
import sys
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
python_exe = sys.executable

print("==================================================")
print("1. STARTING FLASK APPLICATION (run.py)...")
print("==================================================")

server_process = subprocess.Popen(
    [python_exe, "run.py"],
    cwd=str(ROOT_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to be responsive
url_health = "http://127.0.0.1:5000/api/health/db"
url_root = "http://127.0.0.1:5000/"

started = False
for _ in range(30):
    try:
        r = requests.get(url_health, timeout=2)
        if r.status_code == 200:
            started = True
            print("Flask server started and responsive on http://127.0.0.1:5000!")
            break
    except Exception:
        time.sleep(1)

if not started:
    print("FAILED: Flask server did not start in time.")
    server_process.terminate()
    sys.exit(1)

try:
    print("\n==================================================")
    print("2. VERIFYING REGISTERED BLUEPRINTS...")
    print("==================================================")
    # Check directly from app factory
    sys.path.insert(0, str(ROOT_DIR))
    from app import create_app
    app_instance = create_app()
    registered_bps = list(app_instance.blueprints.keys())
    print("Registered Blueprints in Flask App:", registered_bps)
    expected_bps = ["auth", "documents", "access", "admin", "search"]
    for bp in expected_bps:
        assert bp in registered_bps, f"Missing blueprint: {bp}"
        print(f"  [PASS] Blueprint '{bp}' registered successfully")

    print("\n==================================================")
    print("3. VERIFYING FRONTEND ROOT PAGE LOADS (GET /)...")
    print("==================================================")
    root_res = requests.get(url_root, timeout=5)
    print(f"HTTP Status: {root_res.status_code}")
    assert root_res.status_code == 200, f"Expected 200, got {root_res.status_code}"
    assert "Triad DMS" in root_res.text, "Root page did not contain 'Triad DMS'"
    assert "loginForm" in root_res.text, "Root page did not contain 'loginForm'"
    print("  [PASS] Root page GET / loads 200 OK and serves index.html frontend successfully!")

    print("\n==================================================")
    print("4. RUNNING ORIGINAL test_api.py...")
    print("==================================================")
    test_proc = subprocess.run(
        [python_exe, "test_api.py"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True
    )
    print("STDOUT:")
    print(test_proc.stdout)
    if test_proc.stderr:
        print("STDERR:")
        print(test_proc.stderr)

    report_file = ROOT_DIR / "test_report.txt"
    if report_file.exists():
        print("test_report.txt:")
        print(report_file.read_text(encoding="utf-8"))

finally:
    print("\nStopping Flask application...")
    server_process.terminate()
    server_process.wait()
    print("Flask application stopped.")
