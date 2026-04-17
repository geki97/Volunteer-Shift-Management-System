#!/usr/bin/env python
"""Force Flask reload and test QR check-in"""

import sys
import os
from pathlib import Path

# Change to app directory
os.chdir(r"c:\Users\giaco\OneDrive\Desktop\Final Year Proj - Copia\volunteer-management-system")
sys.path.insert(0, os.getcwd())

print("\n" + "="*70)
print(" TESTING QR CHECKIN WITH FRESH FLASK IMPORT")
print("="*70)

# Force remove cached modules to ensure fresh import
for mod_name in list(sys.modules.keys()):
    if 'web' in mod_name or 'check_in' in mod_name:
        del sys.modules[mod_name]

print("\n[1] Creating test Flask app...")
from flask import Flask
from scripts.utils import logger

# Now import the check_in_app - this will load the LATEST version
print("[2] Importing web.check_in_app...")
import web.check_in_app as app_module

# Get the Flask app
app = app_module.app

# Test context
print("\n[3] Testing within Flask app context...")
with app.test_client() as client:
    # Generate a test token
    print("\n[4] Generating test QR token...")
    from scripts.security.qr_secure import SecureQRCode
    
    shift_id = "food_distribution_-_city_centre"
    user_id = "sarah_murphy"
    
    token = SecureQRCode.generate_check_in_token(shift_id, user_id, expiry_hours=1)
    print(f"    Generated token (truncated): {token[:50]}...")
    
    # Make request to check-in endpoint
    print("\n[5] Making request to /check-in/token/<token>...")
    check_in_url = f"/check-in/token/{token}"
    
    response = client.get(check_in_url)
    print(f"    Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[SUCCESS] Got 200 response!")
        
        # Check if shift info is in response
        response_text = response.get_data(as_text=True)
        if "Food Distribution" in response_text or "sarah_murphy" in response_text:
            print("[SUCCESS] Shift information found in response!")
            print("[PASS] QR check-in is working!")
        else:
            print("[WARNING] Response received but no shift info found")
            print(f"Response preview: {response_text[:500]}")
    else:
        print(f"[FAIL] Got status code {response.status_code}")
        response_text = response.get_data(as_text=True)
        print(f"Response: {response_text[:1000]}")
    
    # Also test legacy endpoint
    print("\n[6] Testing legacy /check-in/<shift_id> endpoint...")
    legacy_response = client.get(f"/check-in/{shift_id}")
    print(f"    Status Code: {legacy_response.status_code}")
    
    if legacy_response.status_code == 200:
        print("[SUCCESS] Legacy endpoint working!")
    else:
        print(f"[FAIL] Legacy endpoint returned {legacy_response.status_code}")

print("\n" + "="*70)
print(" TEST COMPLETE")
print("="*70)
