#!/usr/bin/env python
"""
QR Code Check-In System - Demo and QR Code Generator
Generates QR codes for upcoming shifts and demonstrates the check-in flow
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.security.qr_secure import SecureQRCode
import json
import uuid

print("="*80)
print(" QR CODE CHECK-IN SYSTEM - SETUP & DEMO")
print("="*80)

# Load shifts
shifts_file = Path('appflowy_exports/shifts.json')
if not shifts_file.exists():
    print(" Shifts file not found")
    sys.exit(1)

with open(shifts_file) as f:
    shifts = json.load(f)

print(f"\n Found {len(shifts)} shifts")
print("\n" + "="*80)
print("GENERATING QR CODES FOR UPCOMING SHIFTS")
print("="*80)

# Generate QR codes for each shift
for i, shift in enumerate(shifts, 1):
    shift_id = shift.get('id')
    shift_name = shift.get('shift_name')
    shift_date = shift.get('shift_date')
    location = shift.get('location')
    volunteers = shift.get('assigned_volunteers', [])
    
    print(f"\n Shift {i}: {shift_name}")
    print(f"   ID: {shift_id}")
    print(f"   Date: {shift_date}")
    print(f"   Location: {location}")
    print(f"   Volunteers: {len(volunteers)}")
    
    try:
        qr_path, token = SecureQRCode.generate_shift_qr_code(shift_id, shift_name)
        if qr_path:
            print(f"    QR Code Generated: {Path(qr_path).name}")
        else:
            print(f"     Failed to generate QR code")
    except Exception as e:
        print(f"     Error: {e}")

print("\n" + "="*80)
print(" HOW THE CHECK-IN SYSTEM WORKS")
print("="*80)

print("""
STEP 1: Volunteer QR Scan
  → Volunteer scans the printed/displayed QR code
  → Gets directed to: http://localhost:5000/check-in/{shift_id}

STEP 2: Shift Information Display
  → System loads shift details from appflowy_exports/shifts.json
  → Shows:
    • Shift name, date, time
    • Location
    • Shift coordinator
    • Special instructions

STEP 3: Volunteer Selection
  → System loads assigned volunteers from JSON
  → Displays volunteers as clickable cards with:
    • Name
    • Email
    • Skills
  → Volunteer clicks their name to select

STEP 4: Confirmation & Check-In
  → System shows selected volunteer info
  → Volunteer clicks "Confirm Check-In"
  → System records check-in to Supabase database
  → Volunteer sees success page with confirmation

STEP 5: Success Page
  → Shows personalized welcome message
  → Displays next steps
  → Provides coordinator contact info
  → Returns to home option
""")

print("="*80)
print(" WEB INTERFACE SETUP")
print("="*80)

print("""
To start the system:

1. Navigate to the volunteer-management-system directory:
   cd "c:\\Users\\giaco\\OneDrive\\Desktop\\Final Year Proj - Copia\\volunteer-management-system"

2. Start the Flask web server:
   python web\\check_in_app.py
   OR
   start_automation.bat

3. Access the system:
   Home Page:     http://localhost:5000/
   Check-In Page: http://localhost:5000/check-in/{shift_id}

4. For Testing (use shift ID from above):
   Example: http://localhost:5000/check-in/morning_stock_check_-_march_23

FEATURES:
   Volunteer selection by name/skills
   Real-time check-in to database
   Personalized success confirmation
   Shift coordinator contact info
   Special instructions display
   Error handling & validation
""")

print("="*80)
print(" QR CODE SETUP COMPLETE")
print("="*80)

# List generated QR codes
qr_dir = Path('qr_codes')
if qr_dir.exists():
    qr_files = list(qr_dir.glob('*.png'))
    if qr_files:
        print(f"\n Generated QR Code Files ({len(qr_files)}):")
        for qr_file in sorted(qr_files):
            print(f"   • {qr_file.name}")
    else:
        print("\n  No QR codes found in qr_codes/ directory")
else:
    print("\n  qr_codes/ directory not found")

print("\n" + "="*80)
print("Ready to start check-ins! ")
print("="*80 + "\n")
