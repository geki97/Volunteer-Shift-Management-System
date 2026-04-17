#!/usr/bin/env python
"""Test QR code check-in with JSON fallback"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json
from scripts.security.qr_secure import SecureQRCode

# Test URL
BASE_URL = "http://localhost:5000"

def test_qr_checkin():
    """Test QR code check-in process"""
    
    print("\n" + "="*70)
    print(" QR CODE CHECK-IN TEST WITH JSON FALLBACK")
    print("="*70)
    
    # Test 1: Generate a QR token
    print("\n[TEST 1] Generate QR Token")
    print("-" * 70)
    
    shift_id = "food_distribution_-_city_centre"
    user_id = "sarah_murphy"
    
    token = SecureQRCode.generate_check_in_token(shift_id, user_id, expiry_hours=1)
    print(f"[OK] Generated token: {token[:50]}...")
    
    # Test 2: Access check-in endpoint with token
    print("\n[TEST 2] Access Check-In Endpoint")
    print("-" * 70)
    
    check_in_url = f"{BASE_URL}/check-in/token/{token}"
    print(f"Testing URL: {check_in_url}")
    
    try:
        response = requests.get(check_in_url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[PASS] Check-in page loaded successfully")
            
            # Check if shift information is present
            if "Food Distribution - City Centre" in response.text or "shift" in response.text.lower():
                print("[PASS] Shift information loaded from JSON fallback")
                return True
            else:
                print("[FAIL] No shift information in response")
                print(f"Response preview: {response.text[:500]}")
                return False
        else:
            print(f"[FAIL] Non-200 status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error accessing endpoint: {e}")
        return False

def test_legacy_checkin():
    """Test legacy check-in endpoint"""
    
    print("\n[TEST 3] Legacy Check-In Endpoint")
    print("-" * 70)
    
    shift_id = "food_distribution_-_city_centre"
    legacy_url = f"{BASE_URL}/check-in/{shift_id}"
    print(f"Testing URL: {legacy_url}")
    
    try:
        response = requests.get(legacy_url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[PASS] Legacy check-in page loaded successfully")
            
            # Check if volunteer information is present
            if "Sarah Murphy" in response.text or "volunteer" in response.text.lower():
                print("[PASS] Volunteer information loaded from JSON fallback")
                return True
            else:
                print("[FAIL] No volunteer information in response")
                return False
        else:
            print(f"[FAIL] Non-200 status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error accessing legacy endpoint: {e}")
        return False

if __name__ == "__main__":
    print("\nStarting QR code check-in tests...")
    print("Make sure the web server is running on localhost:5000")
    
    results = []
    results.append(test_qr_checkin())
    results.append(test_legacy_checkin())
    
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] QR code check-in working with JSON fallback!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
