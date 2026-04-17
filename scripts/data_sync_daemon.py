"""
Data Sync Daemon
Synchronizes data between AppFlowy and Supabase
"""

import sys
from pathlib import Path

# Add parent directory to path once
sys.path.insert(0, str(Path(__file__).parent.parent))

import schedule
import time
import json
from datetime import datetime
from config.settings import APPFLOWY_EXPORT_PATH, SYNC_INTERVAL_MINUTES
from scripts.utils.logger import logger
from scripts.utils.database import db

def load_appflowy_exports():
    """Load exported volunteers and shifts from AppFlowy JSON files"""
    try:
        volunteers_data = []
        shifts_data = []
        
        # Load volunteers
        volunteers_file = APPFLOWY_EXPORT_PATH / 'volunteers.json'
        if volunteers_file.exists():
            with open(volunteers_file, 'r', encoding='utf-8') as f:
                volunteers_data = json.load(f)
            logger.info(f"📥 Loaded {len(volunteers_data)} volunteers from AppFlowy export")
        
        # Load shifts
        shifts_file = APPFLOWY_EXPORT_PATH / 'shifts.json'
        if shifts_file.exists():
            with open(shifts_file, 'r', encoding='utf-8') as f:
                shifts_data = json.load(f)
            logger.info(f"📥 Loaded {len(shifts_data)} shifts from AppFlowy export")
        
        return volunteers_data, shifts_data
        
    except FileNotFoundError:
        logger.warning("⚠️  AppFlowy JSON files not found - skipping sync")
        return [], []
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in AppFlowy exports: {e}")
        return [], []
    except Exception as e:
        logger.error(f"❌ Error loading AppFlowy exports: {e}")
        return [], []


def parse_appflowy_volunteers(json_file=None):
    """
    Parse volunteers.json exported from AppFlowy
    Returns list of volunteer dictionaries
    
    Args:
        json_file: Optional path to volunteers.json file
    
    Returns:
        List of parsed volunteer dictionaries
    """
    try:
        if json_file is None:
            json_file = APPFLOWY_EXPORT_PATH / 'volunteers.json'
        
        if not json_file.exists():
            logger.warning(f"⚠️  volunteers.json not found at {json_file}")
            return []
        
        with open(json_file, 'r', encoding='utf-8') as f:
            volunteers = json.load(f)
        
        # Transform AppFlowy format to Supabase format if needed
        parsed_volunteers = []
        for vol in volunteers:
            parsed_vol = {
                'appflowy_id': vol.get('id', ''),
                'name': vol.get('name', ''),
                'email': vol.get('email', ''),
                'phone': vol.get('phone', ''),
                'skills': vol.get('skills', []),
                'availability': vol.get('availability', ''),
                'total_shifts_assigned': vol.get('total_shifts_assigned', 0),
                'shifts_completed': vol.get('shifts_completed', 0),
                'no_shows': vol.get('no_shows', 0),
                'cancellations': vol.get('cancellations', 0),
                'reliability_score': float(vol.get('reliability_score', 0.0)),
                'status': vol.get('status', 'Active'),
                'date_registered': vol.get('date_registered', ''),
                'notes': vol.get('notes', '')
            }
            parsed_volunteers.append(parsed_vol)
        
        logger.info(f"✅ Parsed {len(parsed_volunteers)} volunteers from AppFlowy")
        return parsed_volunteers
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in volunteers.json: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error parsing volunteers: {e}")
        return []


def parse_appflowy_shifts(json_file=None):
    """
    Parse shifts.json exported from AppFlowy
    Returns list of shift dictionaries
    
    Args:
        json_file: Optional path to shifts.json file
    
    Returns:
        List of parsed shift dictionaries
    """
    try:
        if json_file is None:
            json_file = APPFLOWY_EXPORT_PATH / 'shifts.json'
        
        if not json_file.exists():
            logger.warning(f"⚠️  shifts.json not found at {json_file}")
            return []
        
        with open(json_file, 'r', encoding='utf-8') as f:
            shifts = json.load(f)
        
        parsed_shifts = []
        for shift in shifts:
            parsed_shift = {
                'appflowy_id': shift.get('id', ''),
                'shift_name': shift.get('shift_name', ''),
                'shift_date': shift.get('shift_date', ''),
                'end_time': shift.get('end_time', ''),
                'location': shift.get('location', ''),
                'required_volunteers': shift.get('required_volunteers', 0),
                'current_assigned': shift.get('current_assigned', 0),
                'status': shift.get('status', 'Open'),
                'priority': shift.get('priority', 'Medium'),
                'volunteer_roles': shift.get('volunteer_roles', []),
                'assigned_volunteers': shift.get('assigned_volunteers', []),
                'shift_coordinator': shift.get('shift_coordinator', ''),
                'special_instructions': shift.get('special_instructions', ''),
                'created_date': shift.get('created_date', '')
            }
            parsed_shifts.append(parsed_shift)
        
        logger.info(f"✅ Parsed {len(parsed_shifts)} shifts from AppFlowy")
        return parsed_shifts
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in shifts.json: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ Error parsing shifts: {e}")
        return []

def sync_volunteers():
    """Sync volunteer data from AppFlowy to Supabase"""
    try:
        logger.info("👥 Syncing volunteers from AppFlowy → Supabase...")
        
        volunteers_data, _ = load_appflowy_exports()
        
        synced = 0
        for volunteer in volunteers_data:
            try:
                appflowy_id = volunteer.get('appflowy_id') or volunteer.get('id')

                # Check if volunteer already exists
                existing = db.get_volunteer_by_appflowy_id(appflowy_id)
                
                # Prepare volunteer data
                volunteer_info = {
                    'appflowy_id': appflowy_id,
                    'name': volunteer.get('name'),
                    'email': volunteer.get('email'),
                    'phone': volunteer.get('phone'),
                    'skills': volunteer.get('skills', []),
                    'availability': volunteer.get('availability'),
                    'status': volunteer.get('status', 'Active'),
                    'notes': volunteer.get('notes', ''),
                }
                
                if existing:
                    # Update existing volunteer
                    db.update_volunteer(
                        appflowy_id=appflowy_id,
                        updates=volunteer_info
                    )
                    logger.info(f"  ✏️ Updated volunteer: {volunteer.get('name')}")
                else:
                    # Create new volunteer
                    db.create_volunteer(volunteer_info)
                    logger.info(f"  ✅ Created volunteer: {volunteer.get('name')}")
                
                synced += 1
                
            except Exception as e:
                logger.error(f"  ❌ Error syncing volunteer {volunteer.get('name')}: {e}")
        
        logger.info(f"✅ Synced {synced}/{len(volunteers_data)} volunteers")
        return synced
        
    except Exception as e:
        logger.error(f"❌ Error in sync_volunteers: {e}")
        return 0

def sync_shifts():
    """Sync shift data from AppFlowy to Supabase"""
    try:
        logger.info("📋 Syncing shifts from AppFlowy → Supabase...")
        
        _, shifts_data = load_appflowy_exports()
        
        synced = 0
        for shift in shifts_data:
            try:
                appflowy_id = shift.get('appflowy_id') or shift.get('id')

                # Check if shift already exists
                existing = db.get_shift_by_appflowy_id(appflowy_id)
                
                # Prepare shift data
                shift_info = {
                    'appflowy_id': appflowy_id,
                    'shift_name': shift.get('shift_name'),
                    'shift_date': shift.get('shift_date'),
                    'end_time': shift.get('end_time'),
                    'location': shift.get('location'),
                    'required_volunteers': shift.get('required_volunteers'),
                    'status': shift.get('status', 'Open'),
                    'priority': shift.get('priority', 'Medium'),
                    'shift_coordinator': shift.get('shift_coordinator'),
                    'special_instructions': shift.get('special_instructions', ''),
                }
                
                if existing:
                    # Update existing shift
                    db.client.table('shifts').update(shift_info).eq('appflowy_id', appflowy_id).execute()
                    logger.info(f"  ✏️ Updated shift: {shift.get('shift_name')}")
                else:
                    # Create new shift
                    db.create_shift(shift_info)
                    logger.info(f"  ✅ Created shift: {shift.get('shift_name')}")
                
                synced += 1
                
            except Exception as e:
                logger.error(f"  ❌ Error syncing shift {shift.get('shift_name')}: {e}")
        
        logger.info(f"✅ Synced {synced}/{len(shifts_data)} shifts")
        return synced
        
    except Exception as e:
        logger.error(f"❌ Error in sync_shifts: {e}")
        return 0

def perform_sync():
    """Perform full sync of all data"""
    try:
        logger.info("="*60)
        logger.info(f"🔄 Data Sync Started at {str(datetime.now())[:19]}")
        logger.info("="*60)
        
        volunteer_count = sync_volunteers()
        shift_count = sync_shifts()
        
        logger.info("="*60)
        logger.info(f"✅ Sync Complete: {volunteer_count} volunteers, {shift_count} shifts")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Error in perform_sync: {e}")

def start_sync_daemon():
    """Start the data sync daemon"""
    from datetime import datetime
    
    logger.info("="*60)
    logger.info("🚀 Starting Data Sync Daemon")
    logger.info(f"📊 Sync interval: every {SYNC_INTERVAL_MINUTES} minutes")
    logger.info("="*60)
    
    # Schedule sync at intervals
    schedule.every(SYNC_INTERVAL_MINUTES).minutes.do(perform_sync)
    
    # Run immediately on startup
    perform_sync()
    
    # Keep daemon running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_sync_daemon()
