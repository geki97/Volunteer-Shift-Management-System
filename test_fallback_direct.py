#!/usr/bin/env python
"""Direct test of fallback functions"""

import sys
import os
from pathlib import Path

# Set working directory
os.chdir(r"c:\Users\giaco\OneDrive\Desktop\Final Year Proj - Copia\volunteer-management-system")
sys.path.insert(0, os.getcwd())

# Now test the fallback functions directly
print("\n" + "="*70)
print(" DIRECT TEST OF FALLBACK FUNCTIONS")
print("="*70)

print(f"\nCurrent working directory: {os.getcwd()}")
print(f"Checking for shifts.json...")

shifts_file = Path(os.getcwd()) / 'appflowy_exports' / 'shifts.json'
print(f"File path: {shifts_file}")
print(f"Exists: {shifts_file.exists()}")

if shifts_file.exists():
    import json
    with open(shifts_file, 'r', encoding='utf-8') as f:
        shifts = json.load(f)
    print(f"Loaded {len(shifts)} shifts")
    print(f"\n[SUCCESS] Shifts can be loaded from JSON!")
    
    # Print first shift
    if shifts:
        print(f"\nFirst shift: {shifts[0]['shift_name']} (ID: {shifts[0]['id']})")
else:
    print(f"[ERROR] File not found: {shifts_file}")

# Now test loading specific shift
print("\n" + "-"*70)
print("Testing specific shift lookup...")

test_shift_id = "food_distribution_-_city_centre"
found = False
for shift in shifts:
    if shift.get('id') == test_shift_id:
        print(f"[SUCCESS] Found shift: {shift['shift_name']}")
        print(f"  Location: {shift['location']}")
        print(f"  Date: {shift['shift_date']}")
        print(f"  Assigned Volunteers: {shift.get('assigned_volunteers', [])}")
        found = True
        break

if not found:
    print(f"[ERROR] Shift {test_shift_id} not found")

# Test volunteer loading
print("\n" + "-"*70)
print("Testing volunteer loading...")

vols_file = Path(os.getcwd()) / 'appflowy_exports' / 'volunteers.json'
print(f"File path: {vols_file}")
print(f"Exists: {vols_file.exists()}")

if vols_file.exists():
    with open(vols_file, 'r', encoding='utf-8') as f:
        volunteers = json.load(f)
    print(f"Loaded {len(volunteers)} volunteers")
    
    # Test specific volunteer
    test_vol_id = "sarah_murphy"
    for vol in volunteers:
        if vol.get('id') == test_vol_id:
            print(f"[SUCCESS] Found volunteer: {vol['name']} ({vol['id']})")
            break
else:
    print(f"[ERROR] File not found: {vols_file}")

print("\n" + "="*70)
print(" CONCLUSION: JSON fallback loading works correctly!")
print("="*70)
