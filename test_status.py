#!/usr/bin/env python
"""Simple system test without emoji"""

import json
import sys
from pathlib import Path

def main():
    """Run a legacy manual status check without executing on import."""
    try:
        from scripts.utils.database import db
        print("[OK] Supabase connected successfully!")
    except Exception as e:
        print(f"[ERROR] Supabase connection failed: {e}")
        sys.exit(1)

    volunteers_file = Path('appflowy_exports/volunteers.json')
    shifts_file = Path('appflowy_exports/shifts.json')

    print("\n" + "="*60)
    print("VOLUNTEER MANAGEMENT SYSTEM - STATUS CHECK")
    print("="*60)

    if volunteers_file.exists():
        with open(volunteers_file) as f:
            volunteers = json.load(f)
        print(f"\n[OK] Volunteers JSON: {len(volunteers)} records")

    if shifts_file.exists():
        with open(shifts_file) as f:
            shifts = json.load(f)
        print(f"[OK] Shifts JSON: {len(shifts)} records")

    volunteer_query_ok = False
    shift_query_ok = False

    try:
        vol_count = len(db.get_all_volunteers(status=None))
        print(f"[OK] Volunteers in Supabase: {vol_count}")
        volunteer_query_ok = True
    except Exception as e:
        print(f"[ERROR] Could not query volunteers: {e}")

    try:
        shift_count = len(db.client.table('shifts').select('*').execute().data)
        print(f"[OK] Shifts in Supabase: {shift_count}")
        shift_query_ok = True
    except Exception as e:
        print(f"[NOTE] Shifts table check: {e}")

    if volunteer_query_ok and shift_query_ok:
        status = "HEALTHY"
    elif volunteer_query_ok or shift_query_ok:
        status = "PARTIAL"
    else:
        status = "NOT OPERATIONAL"

    print("\n" + "="*60)
    print(f"SYSTEM STATUS: {status}")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: start_automation.bat")
    print("2. Access web interface: http://localhost:5000")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
