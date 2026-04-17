#!/usr/bin/env python
"""
Test Twilio SMS Configuration
Sends a test message to verify credentials work properly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.sms_notifier import send_sms
from scripts.utils.logger import logger

def test_twilio():
    """Test Twilio SMS sending"""
    print("[*] Testing Twilio SMS Configuration")
    print("-" * 50)
    
    # Test phone number (your Italian phone)
    to_phone = "+39 3770815088"
    test_message = "Test message from Volunteer Management System - SMS working!"
    
    print(f"[*] Sending SMS to: {to_phone}")
    print(f"[*] Message: {test_message}")
    print()
    
    success, result = send_sms(to_phone, test_message)
    
    if success:
        print(f"[+] SMS Sent Successfully!")
        print(f"[+] Message ID: {result}")
        return True
    else:
        print(f"[!] SMS Failed to Send")
        print(f"[!] Error: {result}")
        return False

if __name__ == "__main__":
    try:
        test_twilio()
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        logger.error(f"Twilio test failed: {e}")
