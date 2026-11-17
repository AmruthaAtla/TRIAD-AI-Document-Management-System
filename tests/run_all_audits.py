import subprocess
import time
import sys
import os
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
python_exe = sys.executable

print("=================================================================")
print("          TRIAD AI DMS - MASTER FINAL SUBMISSION AUDIT           ")
print("=================================================================\n")

# Start Flask server
print("Starting Flask server (run.py)...")
server_proc = subprocess.Popen(
    [python_exe, "run.py"],
    cwd=str(ROOT_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

health_url = "http://127.0.0.1:5000/api/health/db"
started = False
for _ in range(30):
    try:
        r = requests.get(health_url, timeout=2)
        if r.status_code == 200:
            started = True
            print("Flask server successfully running on http://127.0.0.1:5000!\n")
            break
    except Exception:
        time.sleep(1)

if not started:
    print("FAILED to start server.")
    server_proc.terminate()
    sys.exit(1)

audit_results = {}

try:
    # 1. RUN ORIGINAL test_api.py
    print("-----------------------------------------------------------------")
    print("TEST SUITE 1: Original TRIAD AI Starter test_api.py")
    print("-----------------------------------------------------------------")
    p1 = subprocess.run([python_exe, "test_api.py"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    print(p1.stdout)
    if p1.stderr:
        print("STDERR:", p1.stderr)
    report_file = ROOT_DIR / "test_report.txt"
    report_text = report_file.read_text(encoding="utf-8") if report_file.exists() else ""
    passed_1 = 3 if "Passed: 3" in report_text and "Failed: 0" in report_text else 0
    failed_1 = 0 if passed_1 == 3 else 1
    audit_results["test_api.py"] = {"passed": passed_1, "failed": failed_1}

    # 2. RUN NORMAL USER APPROVAL SCENARIO
    print("\n-----------------------------------------------------------------")
    print("TEST SUITE 2: Normal User Cross-Division Approval Scenario")
    print("-----------------------------------------------------------------")
    # We can run test_normal_user_approval internal logic directly since server is already running
    p2 = subprocess.run([python_exe, "tests/run_live_verification.py"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    print(p2.stdout)
    if p2.stderr:
        print("STDERR:", p2.stderr)
    passed_2 = 3 if "[PASS] CHECK 1" in p2.stdout and "[PASS] CHECK 2" in p2.stdout and "[PASS] CHECK 3" in p2.stdout else 0
    failed_2 = 0 if passed_2 == 3 else 1
    audit_results["Cross-Division & Security Checks"] = {"passed": passed_2, "failed": failed_2}

    # 3. RUN FULL END-TO-END REGRESSION SUITE (31 tests)
    print("\n-----------------------------------------------------------------")
    print("TEST SUITE 3: Full 31-Point End-to-End Regression Suite")
    print("-----------------------------------------------------------------")
    p3 = subprocess.run([python_exe, "tests/test_full_system.py"], cwd=str(ROOT_DIR), capture_output=True, text=True)
    print(p3.stdout)
    if p3.stderr:
        print("STDERR:", p3.stderr)
    passed_3 = 31 if "ALL 31 REGRESSION TESTS PASSED!" in p3.stdout else 0
    failed_3 = 0 if passed_3 == 31 else 1
    audit_results["Full Regression Suite"] = {"passed": passed_3, "failed": failed_3}

finally:
    print("\nStopping Flask server...")
    server_proc.terminate()
    server_proc.wait()
    print("Flask server stopped.\n")

print("=================================================================")
print("                   FINAL AUDIT TEST SUMMARY                      ")
print("=================================================================")
total_p = sum(v["passed"] for v in audit_results.values())
total_f = sum(v["failed"] for v in audit_results.values())
for name, res in audit_results.items():
    print(f"- {name}: {res['passed']} Passed, {res['failed']} Failed")
print("-----------------------------------------------------------------")
print(f"TOTAL: {total_p} PASSED, {total_f} FAILED")
print("=================================================================")
