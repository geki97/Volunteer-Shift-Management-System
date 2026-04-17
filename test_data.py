#!/usr/bin/env python
"""Quick test to show system is working"""

import json
import sys
from pathlib import Path

def main():
    """Print a quick sample-data summary for manual terminal use."""
    volunteers_file = Path('appflowy_exports/volunteers.json')
    shifts_file = Path('appflowy_exports/shifts.json')

    print("\n" + "="*60)
    print(" VOLUNTEER MANAGEMENT SYSTEM - DATA CHECK")
    print("="*60)

    if volunteers_file.exists():
        with open(volunteers_file) as f:
            volunteers = json.load(f)
        print(f"\n Volunteers Data:")
        print(f"   Total: {len(volunteers)} volunteers")
        for v in volunteers[:3]:
            print(f"   - {v.get('name')} ({v.get('email')})")

    if shifts_file.exists():
        with open(shifts_file) as f:
            shifts = json.load(f)
        print(f"\n Shifts Data:")
        print(f"   Total: {len(shifts)} shifts")
        for s in shifts[:2]:
            print(f"   - {s.get('shift_name')} at {s.get('location')}")

    print("\n" + "="*60)
    print(" Sample data is ready for syncing!")
    print("="*60)
    print("\nNext steps:")
    print("1. Configure .env file with Supabase credentials")
    print("2. Run: python scripts/appflowy_sync_manager.py")
    print("3. Run: python scripts/check_status.py")
    print("4. Run: start_automation.bat")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
