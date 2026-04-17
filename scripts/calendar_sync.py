"""
Google Calendar Sync
Automatically syncs volunteer shifts to Google Calendar
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
from datetime import datetime
import pytz
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import build
from config.settings import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, TIMEZONE
from scripts.utils.logger import logger
from scripts.utils.database import db

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Cache for service to avoid recreating it
_calendar_service = None

def get_google_calendar_service():
    """
    Get authenticated Google Calendar service (cached)
    
    Returns:
        Google Calendar service object
    """
    global _calendar_service
    
    # Return cached service if available
    if _calendar_service is not None:
        return _calendar_service
    
    try:
        if os.path.exists(GOOGLE_TOKEN_FILE):
            creds = OAuthCredentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
        else:
            # Create new credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        _calendar_service = build('calendar', 'v3', credentials=creds)
        logger.info("Connected to Google Calendar")
        return _calendar_service
        
    except Exception as e:
        logger.error(f"Error connecting to Google Calendar: {e}")
        return None

def sync_shift_to_calendar(shift_data: dict):
    """
    Add or update a shift in Google Calendar
    
    Args:
        shift_data: Shift information from Supabase
    """
    try:
        service = get_google_calendar_service()
        if not service:
            logger.error("Cannot sync - no calendar service")
            return False
        
        tz = pytz.timezone(TIMEZONE)
        shift_date = shift_data['shift_date']
        
        # Create calendar event
        event = {
            'summary': f" {shift_data['shift_name']}",
            'description': f"""
Volunteer Shift
Location: {shift_data.get('location', 'TBD')}
Required Volunteers: {shift_data.get('required_volunteers', 'TBD')}
Coordinator: {shift_data.get('shift_coordinator', 'TBD')}

Instructions: {shift_data.get('special_instructions', 'None')}
            """,
            'start': {
                'dateTime': shift_date,
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': shift_data.get('end_time', shift_date),
                'timeZone': TIMEZONE,
            },
            'location': shift_data.get('location', ''),
            'transparency': 'opaque',  # Show as busy
        }
        
        # Add to calendar
        event_result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        logger.info(f" Shift synced to calendar: {event_result['id']}")
        
        # Store calendar event ID in database for future updates
        # This would require updating the shifts table schema
        
        return True
        
    except Exception as e:
        logger.error(f" Error syncing shift to calendar: {e}")
        return False

def sync_all_shifts():
    """Sync all upcoming shifts to Google Calendar"""
    try:
        logger.info(" Syncing all upcoming shifts to Google Calendar...")
        
        # Get upcoming shifts
        upcoming_shifts = db.get_upcoming_shifts(hours_ahead=30*24)  # Next 30 days
        
        for shift in upcoming_shifts:
            sync_shift_to_calendar(shift)
        
        logger.info(f" Synced {len(upcoming_shifts)} shifts to calendar")
        
    except Exception as e:
        logger.error(f" Error in sync_all_shifts: {e}")

def remove_shift_from_calendar(calendar_event_id: str):
    """Remove a shift from Google Calendar"""
    try:
        service = get_google_calendar_service()
        if not service:
            return False
        
        service.events().delete(
            calendarId='primary',
            eventId=calendar_event_id
        ).execute()
        
        logger.info(f" Shift removed from calendar: {calendar_event_id}")
        return True
        
    except Exception as e:
        logger.error(f" Error removing shift from calendar: {e}")
        return False

if __name__ == "__main__":
    sync_all_shifts()
