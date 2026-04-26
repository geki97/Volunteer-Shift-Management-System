#!/usr/bin/env python
"""
QR Code Check-In System - Demo and QR Code Generator
Generates QR codes for upcoming shifts and demonstrates the check-in flow
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.security.qr_secure import SecureQRCode
from config.settings import APP_BASE_URL
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
base_url = (APP_BASE_URL or "").strip().rstrip("/")
if not base_url or not (base_url.startswith("http://") or base_url.startswith("https://")):
    print("\n[WARN] APP_BASE_URL is not set to an absolute URL.")
    print("       QR codes will contain a non-clickable/relative URL.")
    print("       Set APP_BASE_URL in .env to your GitHub Pages or backend URL.\n")

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
        qr_path, token = SecureQRCode.generate_shift_qr_code(
            shift_id,
            shift_name,
            app_base_url=base_url if base_url else None,
        )
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
  -> Volunteer scans the printed/displayed QR code
  -> Gets directed to: <APP_BASE_URL>/check-in.html?token=<token>

STEP 2: Shift Information Display
  -> System loads shift details from appflowy_exports/shifts.json
  -> Shows:
    - Shift name, date, time
    - Location
    - Shift coordinator
    - Special instructions

STEP 3: Volunteer Selection
  -> System loads assigned volunteers from JSON
  -> Displays volunteers as clickable cards with:
    - Name
    - Email
    - Skills
  -> Volunteer clicks their name to select

STEP 4: Confirmation & Check-In
  -> System shows selected volunteer info
  -> Volunteer clicks "Confirm Check-In"
  -> System records check-in to Supabase (or local fallback log if DB is down)
  -> Volunteer sees success page with confirmation

STEP 5: Success Page
  -> Shows personalized welcome message
  -> Displays next steps
  -> Provides coordinator contact info
  -> Returns to home option
""")

print("="*80)
print(" WEB INTERFACE SETUP")
print("="*80)

print("""
To start the system:

1. Navigate to the volunteer-management-system directory:
   cd "c:\\Users\\giaco\\OneDrive\\Desktop\\Final Year Proj - Copia\\volunteer-management-system"

2. Configure hosted URLs:
   - Set APP_BASE_URL in .env to your hosted site (GitHub Pages) or backend base URL.

3. Access the static site on GitHub Pages:
   Home Page:     <APP_BASE_URL>/
   Check-In Link: <APP_BASE_URL>/check-in.html?token=<token>

4. For Testing (use shift ID from above):
   Use scripts/send_test_qr_email.py --dry-run to generate a QR + preview email.

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
            print(f"   - {qr_file.name}")
    else:
        print("\n  No QR codes found in qr_codes/ directory")
else:
    print("\n  qr_codes/ directory not found")

print("\n" + "="*80)
print("Ready to start check-ins! ")
print("="*80 + "\n")
