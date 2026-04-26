"""
System Status Checker
Monitor system health and display metrics.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import APPFLOWY_EXPORT_PATH, LOG_FILE_PATH
from scripts.utils.database import db
from scripts.utils.logger import setup_logger

logger = setup_logger("check_status")


def _safe_print(*args, sep=" ", end="\n"):
    """Write console output without crashing on narrow Windows encodings."""
    text = sep.join(str(arg) for arg in args) + end
    stream = sys.stdout
    try:
        stream.write(text)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "utf-8"
        stream.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))


print = _safe_print


def check_system_status():
    """Check system status and display health metrics."""
    print("\n" + "=" * 70)
    print("VOLUNTEER MANAGEMENT SYSTEM - STATUS CHECK")
    print("=" * 70)

    status_report = {
        "timestamp": datetime.now().isoformat(),
        "appflowy_exports": {},
        "supabase": {},
        "system_health": "UNKNOWN",
        "issues": [],
    }

    print("\nAppFlowy Exports:")
    print("-" * 70)

    volunteers_file = Path(APPFLOWY_EXPORT_PATH) / "volunteers.json"
    shifts_file = Path(APPFLOWY_EXPORT_PATH) / "shifts.json"

    volunteers_ok = False
    shifts_ok = False

    if volunteers_file.exists():
        try:
            with open(volunteers_file, encoding="utf-8") as f:
                vol_data = json.load(f)
            print(f"   [OK] volunteers.json: {len(vol_data)} records")
            status_report["appflowy_exports"]["volunteers"] = {
                "exists": True,
                "count": len(vol_data),
                "size_kb": volunteers_file.stat().st_size / 1024,
            }
            volunteers_ok = True
        except json.JSONDecodeError:
            print("   [ERROR] volunteers.json: INVALID JSON")
            status_report["issues"].append("volunteers.json has invalid JSON format")
    else:
        print("   [WARN] volunteers.json: NOT FOUND")
        status_report["appflowy_exports"]["volunteers"] = {
            "exists": False,
            "count": 0,
        }
        status_report["issues"].append("volunteers.json not found - export from AppFlowy first")

    if shifts_file.exists():
        try:
            with open(shifts_file, encoding="utf-8") as f:
                shift_data = json.load(f)
            print(f"   [OK] shifts.json: {len(shift_data)} records")
            status_report["appflowy_exports"]["shifts"] = {
                "exists": True,
                "count": len(shift_data),
                "size_kb": shifts_file.stat().st_size / 1024,
            }
            shifts_ok = True
        except json.JSONDecodeError:
            print("   [ERROR] shifts.json: INVALID JSON")
            status_report["issues"].append("shifts.json has invalid JSON format")
    else:
        print("   [WARN] shifts.json: NOT FOUND")
        status_report["appflowy_exports"]["shifts"] = {
            "exists": False,
            "count": 0,
        }
        status_report["issues"].append("shifts.json not found - export from AppFlowy first")

    print("\nSupabase Database:")
    print("-" * 70)

    db_ok = False
    health_check = getattr(db, "check_connection_status", None)
    if health_check is not None:
        is_connected, db_details = health_check()
    else:
        is_connected, db_details = False, {"error": "Database health check unavailable"}

    if is_connected:
        volunteers_count = db_details.get("volunteers_count", 0)
        shifts_count = db_details.get("shifts_count", 0)

        print("   [OK] Connected to Supabase")
        print(f"   Volunteers in DB: {volunteers_count}")
        print(f"   Shifts in DB: {shifts_count}")

        status_report["supabase"]["connected"] = True
        status_report["supabase"]["volunteers_count"] = volunteers_count
        status_report["supabase"]["shifts_count"] = shifts_count

        # Only use the broader helper once connectivity itself has succeeded.
        volunteers = db.get_all_volunteers(status=None)
        no_email = [volunteer for volunteer in volunteers if not volunteer.get("email")]
        if no_email:
            print(f"   [WARN] Volunteers without email: {len(no_email)}")
            status_report["issues"].append(f"{len(no_email)} volunteers missing email addresses")

        db_ok = True
    else:
        error = db_details.get("error", "Unknown database error")
        print(f"   [ERROR] Database Error: {error[:100]}")
        status_report["supabase"]["connected"] = False
        status_report["supabase"]["error"] = error
        status_report["issues"].append(f"Cannot connect to Supabase: {error[:100]}")

    print("\nRecent Activity (Last 5 log entries):")
    print("-" * 70)

    log_files = list(LOG_FILE_PATH.glob("*.log"))
    if log_files:
        latest_log = max(log_files, key=lambda path: path.stat().st_mtime)
        print(f"   Latest Log: {latest_log.name}")

        try:
            with open(latest_log, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            recent = lines[-5:] if len(lines) > 5 else lines
            for line in recent:
                clean_line = line.strip()[:65]
                print(f"      {clean_line}")

            status_report["logs"] = {
                "latest_file": latest_log.name,
                "total_files": len(log_files),
            }
        except Exception as exc:
            print(f"   [WARN] Could not read logs: {exc}")
    else:
        print("   [WARN] No log files found")
        status_report["logs"] = {"files": 0}

    print("\nSystem Health:")
    print("-" * 70)

    if volunteers_ok and shifts_ok and db_ok:
        status = "[OK] HEALTHY"
        status_report["system_health"] = "HEALTHY"
    elif db_ok:
        status = "[WARN] PARTIAL (Database OK, Missing AppFlowy exports)"
        status_report["system_health"] = "PARTIAL"
    elif volunteers_ok or shifts_ok:
        status = "[WARN] PARTIAL (AppFlowy exports available, No database)"
        status_report["system_health"] = "PARTIAL"
    else:
        status = "[ERROR] NOT OPERATIONAL"
        status_report["system_health"] = "CRITICAL"

    print(f"   Status: {status}")

    if status_report["issues"]:
        print(f"\nIssues Found ({len(status_report['issues'])}):")
        for index, issue in enumerate(status_report["issues"], 1):
            print(f"   {index}. {issue}")

    print("\nNext Steps:")
    print("-" * 70)

    if not volunteers_ok or not shifts_ok:
        print("   1. Export Volunteers & Shifts from AppFlowy:")
        print("      - Open AppFlowy workspace")
        print("      - Export Volunteers table to CSV")
        print("      - Export Shifts table to CSV")
        print("      - Save to: appflowy_exports/")
        print()
        print("   2. Convert CSV to JSON:")
        print("      python scripts/csv_to_json_converter.py")
        print()

    if db_ok and (volunteers_ok or shifts_ok):
        print("   Sync data to Supabase:")
        print("      python scripts/appflowy_sync_manager.py")
        print()

    if db_ok and volunteers_ok and shifts_ok:
        print("   Start automation system:")
        print("      start_automation.bat (Windows)")
        print("      or")
        print("      ./start_automation.sh (Mac/Linux)")
        print()

    print("=" * 70)
    print()

    return status_report


def print_status_summary(report):
    """Print a machine-readable summary."""
    summary = {
        "health": report["system_health"],
        "issues_count": len(report["issues"]),
        "exports": report["appflowy_exports"],
        "database": report["supabase"],
        "timestamp": report["timestamp"],
    }
    return json.dumps(summary, indent=2)


if __name__ == "__main__":
    report = check_system_status()

    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print("\n" + print_status_summary(report))
