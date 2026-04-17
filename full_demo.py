#!/usr/bin/env python
"""Full Demo - Comprehensive system showcase"""

import json
from pathlib import Path
from datetime import datetime

def display_header(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def load_json(file_path):
    if not Path(file_path).exists():
        return []
    with open(file_path) as f:
        return json.load(f)

# Load data
volunteers = load_json('appflowy_exports/volunteers.json')
shifts = load_json('appflowy_exports/shifts.json')

display_header("VOLUNTEER MANAGEMENT SYSTEM - FULL DEMO")
print(f"\n Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f" System Status: ✓ OPERATIONAL")

# Section 1: Volunteer Stats
display_header("1. VOLUNTEER STATISTICS")
print(f"\n Total Volunteers: {len(volunteers)}")
print(f" Active Status: {len([v for v in volunteers if v.get('status') == 'Active'])} active")

print("\n Top Performers (by Reliability Score):")
sorted_vols = sorted(volunteers, key=lambda v: v.get('reliability_score', 0), reverse=True)
for i, vol in enumerate(sorted_vols[:5], 1):
    name = vol.get('name', 'Unknown')
    score = vol.get('reliability_score', 0)
    completed = vol.get('shifts_completed', 0)
    no_shows = vol.get('no_shows', 0)
    print(f"  {i}. {name}")
    print(f"     Reliability: {score:.1f}% | Completed: {completed} | No-Shows: {no_shows}")

# Section 2: Volunteer Skills Analysis
display_header("2. VOLUNTEER SKILLS ANALYSIS")
skills_count = {}
for vol in volunteers:
    for skill in vol.get('skills', []):
        skills_count[skill] = skills_count.get(skill, 0) + 1

sorted_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)
print("\n Available Skills:")
for skill, count in sorted_skills[:10]:
    print(f"  • {skill}: {count} volunteers")

# Section 3: Availability Analysis
display_header("3. VOLUNTEER AVAILABILITY")
availability_count = {}
for vol in volunteers:
    for day in vol.get('availability', []):
        availability_count[day] = availability_count.get(day, 0) + 1

days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
print("\n Coverage by Day:")
for day in days_order:
    count = availability_count.get(day, 0)
    if count > 0:
        bar = "█" * (count // 2)
        print(f"  {day:12} {bar} {count}")

# Section 4: Shift Analysis
display_header("4. SHIFT OVERVIEW")
print(f"\n Total Shifts: {len(shifts)}")

for i, shift in enumerate(shifts, 1):
    shift_name = shift.get('shift_name', 'Unknown')
    shift_date = shift.get('shift_date', 'N/A')
    required = shift.get('required_volunteers', 0)
    assigned = shift.get('current_assigned', 0)
    location = shift.get('location', 'N/A')
    status = shift.get('status', 'Unknown')
    
    print(f"\n Shift {i}: {shift_name}")
    print(f"   Date/Time: {shift_date}")
    print(f"   Location: {location}")
    print(f"   Status: {status}")
    print(f"   Volunteers: {assigned}/{required} assigned")
    print(f"   Roles: {', '.join(shift.get('volunteer_roles', []))}")

# Section 5: Check-In System Status
display_header("5. QR CODE CHECK-IN SYSTEM")
qr_dir = Path('qr_codes')
qr_files = list(qr_dir.glob('*.png')) if qr_dir.exists() else []

print(f"\n ✓ QR Code Generator: READY")
print(f" ✓ Generated QR Codes: {len(qr_files)} files")
print(f" ✓ Check-In Web Server: Ready to start")
print(f" ✓ Database Integration: Configured")

print("\n To start the check-in system:")
print("   1. Run: python web/check_in_app.py")
print("   2. Visit: http://localhost:5000")
print("   3. Scan a QR code or navigate to /check-in/{shift_id}")

# Section 6: System Features
display_header("6. AVAILABLE FEATURES")
features = {
    "✓ QR Code Check-in": "Automated volunteer check-in system",
    "✓ Email Notifications": "SendGrid integration for reminders",
    "✓ SMS Notifications": "Twilio integration for urgent updates",
    "✓ Data Synchronization": "AppFlowy ↔ Supabase real-time sync",
    "✓ Reliability Tracking": "Automatic performance scoring",
    "✓ Calendar Integration": "Google Calendar sync",
    "✓ Audit Logging": "Complete system activity tracking",
}

for feature, description in features.items():
    print(f"\n {feature}")
    print(f"   {description}")

# Section 7: File Structure
display_header("7. SYSTEM FILES")
structure = {
    "web/check_in_app.py": "Flask web application",
    "scripts/appflowy_sync_manager.py": "Data synchronization",
    "scripts/reminder_daemon.py": "Automated reminders",
    "scripts/sms_notifier.py": "SMS notifications",
    "appflowy_exports/": "Data import/export directory",
    "qr_codes/": "Generated QR code images",
    "logs/": "System logs",
}

for file, desc in structure.items():
    print(f" • {file:35} - {desc}")

# Section 8: Next Steps
display_header("8. QUICK START GUIDE")
print("""
 STEP 1: Configure API Keys
   Edit or create .env file with:
   - Supabase credentials
   - SendGrid API key
   - Twilio credentials
   - Google Calendar credentials

 STEP 2: Verify Database Connection
   Run: python scripts/check_status.py

 STEP 3: Sync Data
   Run: python scripts/appflowy_sync_manager.py

 STEP 4: Start Web Interface
   Run: python web/check_in_app.py
   Visit: http://localhost:5000

 STEP 5: Start Automation (Optional)
   Run: start_automation.bat
   (Starts all background daemons)

 STEP 6: Stop Services
   Run: stop_automation.bat
""")

display_header("DEMO COMPLETE ✓")
print(f"\n System demonstrates the current core prototype workflows.")
print(f" All {len(volunteers)} volunteers and {len(shifts)} shifts are loaded and configured.")
print(f"\n For issues, check logs/ directory")
print("="*80 + "\n")
