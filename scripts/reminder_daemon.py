"""
Automated Reminder Daemon
Sends email reminders with QR codes 24 hours before shifts
SECURITY: Uses signed QR codes with expiration
"""

import sys
from pathlib import Path

# Add parent directory to path once
sys.path.insert(0, str(Path(__file__).parent.parent))

import schedule
import time
from datetime import datetime, timedelta
import pytz
from config.settings import TIMEZONE, REMINDER_HOURS_BEFORE, APP_BASE_URL
from scripts.utils.logger import logger
from scripts.utils.database import db
from scripts.utils.email_service_enhanced import send_reminder_email_to_volunteer
from scripts.security import SecureQRCode

def send_shift_reminders():
    """Check for upcoming shifts and send reminders with QR codes"""
    try:
        logger.info("Checking for upcoming shifts needing reminders...")
        
        # Get shifts in the next X hours
        upcoming_shifts = db.get_upcoming_shifts(hours_ahead=REMINDER_HOURS_BEFORE)
        
        if not upcoming_shifts:
            logger.info("No upcoming shifts found for reminders")
            return
        
        email_count = 0
        failed_count = 0
        
        for shift in upcoming_shifts:
            # Get volunteers assigned to this shift
            assignments = db.get_shift_assignments(shift['id'])
            
            if not assignments:
                continue
            
            for assignment in assignments:
                try:
                    volunteer = assignment.get('volunteers', {})
                    volunteer_email = volunteer.get('email')
                    volunteer_name = volunteer.get('name')
                    volunteer_id = volunteer.get('id')
                    
                    if not volunteer_email or not volunteer_name or not volunteer_id:
                        logger.warning(f"Missing volunteer info for assignment: {assignment}")
                        continue
                    
                    # SECURITY: Generate secure QR code token for this volunteer
                    qr_path, token = SecureQRCode.generate_shift_qr_code(
                        shift_id=shift['id'],
                        shift_name=shift.get('shift_name', 'Shift'),
                        user_id=volunteer_id,
                        expiry_hours=25,  # QR code valid for 25 hours
                        app_base_url=APP_BASE_URL
                    )
                    
                    if not token:
                        logger.error(f"Failed to generate QR token for volunteer {volunteer_id}")
                        failed_count += 1
                        continue
                    
                    # Send reminder email with QR code
                    success, message_id = send_reminder_email_to_volunteer(
                        volunteer_name=volunteer_name,
                        volunteer_email=volunteer_email,
                        shift_name=shift.get('shift_name', 'Unknown'),
                        shift_date=shift.get('shift_date', '').split('T')[0] if 'T' in shift.get('shift_date', '') else shift.get('shift_date', 'Unknown'),
                        shift_time=shift.get('shift_date', '').split('T')[1][:5] if 'T' in shift.get('shift_date', '') else 'Unknown',
                        location=shift.get('location', 'TBD'),
                        qr_code_path=qr_path,
                        special_instructions=shift.get('special_instructions', '')
                    )
                    
                    # Log notification
                    db.log_notification(
                        notification_type='email',
                        recipient_id=volunteer_id,
                        shift_id=shift['id'],
                        status='sent' if success else 'failed',
                        message_id=message_id if success else None,
                        error=message_id if not success else None
                    )
                    
                    if success:
                        email_count += 1
                        logger.info(f" Reminder sent to {volunteer_name} ({volunteer_email})")
                    else:
                        failed_count += 1
                        logger.error(f" Failed to send reminder: {message_id}")
                        
                except Exception as e:
                    logger.error(f"Error sending reminder for volunteer: {e}")
                    failed_count += 1
        
        logger.info(f"Reminder check complete: {email_count} sent, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Error in send_shift_reminders: {e}")

def start_reminder_daemon():
    """Start the reminder daemon"""
    logger.info("="*60)
    logger.info(" Starting Reminder Daemon")
    logger.info(f" Reminders will be sent {REMINDER_HOURS_BEFORE} hours before shifts")
    logger.info(" QR codes are cryptographically signed with expiration")
    logger.info("="*60)
    
    # Schedule reminder checks every hour
    schedule.every().hour.do(send_shift_reminders)
    
    # Run immediately on startup
    send_shift_reminders()
    
    # Keep daemon running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_reminder_daemon()
