"""
SMS Notifier
Sends SMS notifications via Twilio for urgent alerts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
from twilio.rest import Client
from config.settings import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
from scripts.utils.logger import logger
from scripts.utils.database import db

# Phone number validation regex (international format)
PHONE_REGEX = re.compile(r'^\+\d{10,15}$')

def validate_phone(phone: str) -> bool:
    """Validate phone number format (must be in +1234567890 format)"""
    # Remove spaces for validation
    cleaned = phone.replace(' ', '').replace('-', '')
    return PHONE_REGEX.match(cleaned) is not None

def send_sms(to_phone: str, message: str) -> tuple:
    """
    Send SMS via Twilio
    
    Args:
        to_phone: Recipient phone number in format +1234567890
        message: Message text (max 160 characters for 1 SMS)
    
    Returns:
        tuple: (success: bool, message_id: str or error: str)
    """
    if not validate_phone(to_phone):
        logger.error(f"Invalid phone format: {to_phone}. Use +1234567890 format")
        return False, "Invalid phone format"
    
    try:
        # Clean phone number (remove spaces and dashes)
        cleaned_phone = to_phone.replace(' ', '').replace('-', '')
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        sms_message = client.messages.create(
            body=message[:160],  # Limit to 160 chars
            from_=TWILIO_PHONE_NUMBER,
            to=cleaned_phone
        )
        
        logger.info(f"SMS sent to {to_phone}")
        return True, sms_message.sid
          
    except Exception as e:
        logger.error(f"SMS error to {to_phone}: {e}")
        return False, str(e)

def notify_shift_cancellation(shift_id: str, reason: str = ""):
    """Send SMS notification about shift cancellation"""
    try:
        logger.info(f"📢 Notifying volunteers of shift cancellation: {shift_id}")
        
        # Get shift details
        # Note: Would need to fetch from database using shift_id
        assignments = db.get_shift_assignments(shift_id)
        
        for assignment in assignments:
            volunteer = assignment.get('volunteers', {})
            phone = volunteer.get('phone')
            name = volunteer.get('name')
            
            if not phone:
                logger.warning(f"No phone for volunteer: {name}")
                continue
            
            message = f"Hello {name.split()[0]}, your volunteer shift has been cancelled. {reason}"
            success, msg_id = send_sms(phone, message)
            
            # Log notification
            db.log_notification(
                notification_type='sms',
                recipient_id=volunteer['id'],
                shift_id=shift_id,
                status='sent' if success else 'failed',
                message_id=msg_id if success else None,
                error=msg_id if not success else None
            )
        
        logger.info("Shift cancellation notifications sent")
        
    except Exception as e:
        logger.error(f"Error in notify_shift_cancellation: {e}")

def notify_urgent_request(volunteer_id: str, shift_id: str, urgency: str = "high"):
    """Send urgent shift coverage request via SMS"""
    try:
        logger.info(f"🚨 Sending urgent request SMS to volunteer: {volunteer_id}")
        
        # Get volunteer and shift details
        # Note: would need helper function to get volunteer by ID
        message = "🚨 URGENT: We need your help covering a shift! Please check your email for details and confirm ASAP."
        
        # This would require fetching volunteer phone from database
        logger.info("Will implement with full volunteer lookup")
        
    except Exception as e:
        logger.error(f"Error in notify_urgent_request: {e}")

if __name__ == "__main__":
    # Test SMS
    success, msg_id = send_sms("+351912345678", "Test message from Volunteer System")
    if success:
        print(f"Test SMS sent successfully: {msg_id}")
    else:
        print(f"Test SMS failed: {msg_id}")
