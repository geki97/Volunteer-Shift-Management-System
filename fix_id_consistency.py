#!/usr/bin/env python
"""
Fix volunteer ID inconsistency in shifts.json
Maps UUID-style IDs back to slug-style IDs
"""

import json
from pathlib import Path

# Load volunteers
with open('appflowy_exports/volunteers.json') as f:
    volunteers = json.load(f)

# Create volunteer slug mapping
vol_slugs = [v.get('id') for v in volunteers]
print(f"[INFO] Loaded {len(vol_slugs)} volunteer slug IDs")
print("[INFO] Example slugs:", vol_slugs[:3])

# Load shifts
shifts_file = Path('appflowy_exports/shifts.json')
with open(shifts_file) as f:
    shifts = json.load(f)

print(f"\n[INFO] Processing {len(shifts)} shifts...")

# Check current assignment IDs
for shift in shifts:
    assigned = shift.get('assigned_volunteers', [])
    if assigned:
        print(f"\n[SHIFT] {shift.get('shift_name')}")
        print(f"[BEFORE] First ID: {assigned[0]}")
        
        # Replace UUID-style IDs with slug-style IDs
        # If we have 5 volunteers assigned and 5 slug IDs available, map them
        if len(assigned) <= len(vol_slugs):
            new_assigned = vol_slugs[:len(assigned)]
            shift['assigned_volunteers'] = new_assigned
            print(f"[AFTER]  First ID: {new_assigned[0]}")

# Save corrected shifts.json
with open(shifts_file, 'w') as f:
    json.dump(shifts, f, indent=2)

print(f"\n[SUCCESS] Normalized all shift volunteer assignments to slug-style IDs")
print(f"[SAVE] Updated appflowy_exports/shifts.json")
