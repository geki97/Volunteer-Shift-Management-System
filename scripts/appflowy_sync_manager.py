"""
AppFlowy Sync Manager
Handles bidirectional sync between AppFlowy and Supabase
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.database import db
from scripts.utils.logger import setup_logger
from config.settings import APPFLOWY_EXPORT_PATH

logger = setup_logger('appflowy_sync')


class AppFlowySync:
    """Manages bidirectional sync between AppFlowy and Supabase"""
    
    def __init__(self):
        self.export_path = Path(APPFLOWY_EXPORT_PATH)
        self.volunteers_file = self.export_path / 'volunteers.json'
        self.shifts_file = self.export_path / 'shifts.json'
    
    def parse_appflowy_volunteers(self):
        """
        Parse volunteers.json exported from AppFlowy
        Returns list of volunteer dictionaries
        """
        try:
            if not self.volunteers_file.exists():
                logger.warning(f"volunteers.json not found at {self.volunteers_file}")
                return []
            
            with open(self.volunteers_file, 'r', encoding='utf-8') as f:
                volunteers = json.load(f)
            
            # Transform AppFlowy format to Supabase format
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
                    'reliability_score': vol.get('reliability_score', 0.0),
                    'status': vol.get('status', 'Active'),
                    'date_registered': vol.get('date_registered', ''),
                    'notes': vol.get('notes', '')
                }
                parsed_volunteers.append(parsed_vol)
            
            logger.info(f"Parsed {len(parsed_volunteers)} volunteers from AppFlowy")
            return parsed_volunteers
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in volunteers.json: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing volunteers: {e}")
            return []
    
    def parse_appflowy_shifts(self):
        """
        Parse shifts.json exported from AppFlowy
        Returns list of shift dictionaries
        """
        try:
            if not self.shifts_file.exists():
                logger.warning(f"shifts.json not found at {self.shifts_file}")
                return []
            
            with open(self.shifts_file, 'r', encoding='utf-8') as f:
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
            
            logger.info(f"Parsed {len(parsed_shifts)} shifts from AppFlowy")
            return parsed_shifts
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in shifts.json: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing shifts: {e}")
            return []
    
    def sync_from_appflowy_to_supabase(self):
        """
        Main sync: AppFlowy → Supabase
        Reads JSON exports and updates Supabase
        """
        logger.info("="*60)
        logger.info("Starting AppFlowy to Supabase sync...")
        logger.info("="*60)
        
        stats = {
            'volunteers_created': 0,
            'volunteers_updated': 0,
            'shifts_created': 0,
            'shifts_updated': 0,
            'assignments_created': 0,
            'errors': []
        }
        
        # SYNC VOLUNTEERS
        volunteers = self.parse_appflowy_volunteers()
        for vol in volunteers:
            try:
                existing = db.get_volunteer_by_appflowy_id(vol['appflowy_id'])
                
                if existing:
                    # Update existing volunteer
                    db.update_volunteer(vol['appflowy_id'], vol)
                    stats['volunteers_updated'] += 1
                    logger.info(f"Updated: {vol['name']}")
                else:
                    # Create new volunteer
                    db.create_volunteer(vol)
                    stats['volunteers_created'] += 1
                    logger.info(f"  Created: {vol['name']}")
                    
            except Exception as e:
                logger.error(f" Error syncing volunteer {vol.get('name')}: {e}")
                stats['errors'].append(f"Volunteer {vol.get('name')}: {str(e)}")
        
        # SYNC SHIFTS
        shifts = self.parse_appflowy_shifts()
        for shift in shifts:
            try:
                existing = db.get_shift_by_appflowy_id(shift['appflowy_id'])
                
                if existing:
                    # Update existing shift
                    db.client.table('shifts').update({
                        'shift_name': shift['shift_name'],
                        'shift_date': shift['shift_date'],
                        'end_time': shift['end_time'],
                        'location': shift['location'],
                        'required_volunteers': shift['required_volunteers'],
                        'status': shift['status'],
                        'priority': shift['priority'],
                        'shift_coordinator': shift['shift_coordinator'],
                        'special_instructions': shift['special_instructions'],
                        'volunteer_roles': shift['volunteer_roles']
                    }).eq('appflowy_id', shift['appflowy_id']).execute()
                    
                    stats['shifts_updated'] += 1
                    logger.info(f"Updated: {shift['shift_name']}")
                else:
                    # Create new shift
                    db.create_shift(shift)
                    stats['shifts_created'] += 1
                    logger.info(f"  Created: {shift['shift_name']}")
                
                # SYNC ASSIGNMENTS
                self._sync_assignments(shift)
                stats['assignments_created'] += len(shift.get('assigned_volunteers', []))
                
            except Exception as e:
                logger.error(f"Error syncing shift {shift.get('shift_name')}: {e}")
                stats['errors'].append(f"Shift {shift.get('shift_name')}: {str(e)}")
        
        logger.info("="*60)
        logger.info(f"Sync complete:")
        logger.info(f"   👥 Volunteers: {stats['volunteers_created']} created, {stats['volunteers_updated']} updated")
        logger.info(f"Shifts: {stats['shifts_created']} created, {stats['shifts_updated']} updated")
        logger.info(f"   📍 Assignments: {stats['assignments_created']}")
        if stats['errors']:
            logger.warning(f"Errors: {len(stats['errors'])}")
        logger.info("="*60)
        
        return stats
    
    def sync_from_supabase_to_appflowy(self):
        """
        Reverse sync: Supabase → AppFlowy
        Generates JSON files for import back to AppFlowy
        """
        logger.info("="*60)
        logger.info("Starting Supabase to AppFlowy sync...")
        logger.info("="*60)
        
        try:
            # Get all data from Supabase
            volunteers = db.get_all_volunteers(status=None)  # Get all, not just Active
            shifts = db.get_all_shifts() if hasattr(db, 'get_all_shifts') else []
            
            # Transform to AppFlowy format
            appflowy_volunteers = []
            for vol in volunteers:
                appflowy_vol = {
                    'id': vol.get('appflowy_id', ''),
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
                    'notes': vol.get('notes', ''),
                    'last_updated': vol.get('updated_at', datetime.now().isoformat())
                }
                appflowy_volunteers.append(appflowy_vol)
            
            appflowy_shifts = []
            for shift in shifts:
                try:
                    # Get assigned volunteers for this shift
                    assignments = db.get_shift_assignments(shift.get('id', ''))
                    assigned_vol_ids = [a.get('volunteers', {}).get('appflowy_id', '') 
                                       for a in assignments if a.get('volunteers')]
                    
                    appflowy_shift = {
                        'id': shift.get('appflowy_id', ''),
                        'shift_name': shift.get('shift_name', ''),
                        'shift_date': shift.get('shift_date', ''),
                        'end_time': shift.get('end_time', ''),
                        'location': shift.get('location', ''),
                        'required_volunteers': shift.get('required_volunteers', 0),
                        'current_assigned': len(assigned_vol_ids),
                        'status': shift.get('status', 'Open'),
                        'priority': shift.get('priority', 'Medium'),
                        'volunteer_roles': shift.get('volunteer_roles', []),
                        'assigned_volunteers': assigned_vol_ids,
                        'shift_coordinator': shift.get('shift_coordinator', ''),
                        'special_instructions': shift.get('special_instructions', ''),
                        'created_date': shift.get('created_at', ''),
                        'last_updated': shift.get('updated_at', datetime.now().isoformat())
                    }
                    appflowy_shifts.append(appflowy_shift)
                except Exception as e:
                    logger.error(f"Error processing shift {shift.get('shift_name', '')}: {e}")
            
            # Write to JSON files with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            updated_volunteers_file = self.export_path / f'updated_volunteers_{timestamp}.json'
            updated_shifts_file = self.export_path / f'updated_shifts_{timestamp}.json'
            
            self._save_json(appflowy_volunteers, updated_volunteers_file)
            self._save_json(appflowy_shifts, updated_shifts_file)
            
            logger.info("="*60)
            logger.info(f"Generated updated JSON files:")
            logger.info(f"   📄 {updated_volunteers_file.name} ({len(appflowy_volunteers)} records)")
            logger.info(f"   📄 {updated_shifts_file.name} ({len(appflowy_shifts)} records)")
            logger.info("="*60)
            
            return {
                'volunteers_file': str(updated_volunteers_file),
                'shifts_file': str(updated_shifts_file),
                'volunteers_count': len(appflowy_volunteers),
                'shifts_count': len(appflowy_shifts),
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Error in sync_from_supabase_to_appflowy: {e}")
            return {}
    
    def _sync_assignments(self, shift):
        """Sync volunteer assignments for a shift"""
        try:
            shift_appflowy_id = shift.get('id', '')
            assigned_volunteer_ids = shift.get('assigned_volunteers', [])
            
            if not assigned_volunteer_ids:
                return
            
            # Get shift UUID from Supabase using appflowy_id
            shift_record = db.get_shift_by_appflowy_id(shift_appflowy_id)
            if not shift_record:
                logger.warning(f"Shift {shift_appflowy_id} not found in Supabase")
                return
            
            shift_uuid = shift_record.get('id', '')
            
            # Get current assignments
            current_assignments = db.get_shift_assignments(shift_uuid)
            current_vol_ids = [a.get('volunteer_id', '') for a in current_assignments]
            
            # Create new assignments
            for vol_appflowy_id in assigned_volunteer_ids:
                volunteer = db.get_volunteer_by_appflowy_id(vol_appflowy_id)
                if volunteer:
                    vol_uuid = volunteer.get('id', '')
                    if vol_uuid not in current_vol_ids:
                        db.create_assignment(shift_uuid, vol_uuid)
                        logger.info(f"    📍 Assigned {volunteer.get('name', '')} to {shift.get('shift_name', '')}")
                        
        except Exception as e:
            logger.error(f"Error syncing assignments for shift: {e}")
    
    def _load_json(self, file_path):
        """Load JSON file safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []
    
    def _save_json(self, data, file_path):
        """Save JSON file safely"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved: {file_path}")
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")


def run_bidirectional_sync():
    """Run complete bidirectional sync"""
    try:
        sync = AppFlowySync()
        
        # AppFlowy → Supabase
        appflowy_stats = sync.sync_from_appflowy_to_supabase()
        
        # Supabase → AppFlowy (generate updated files)
        supabase_stats = sync.sync_from_supabase_to_appflowy()
        
        return {
            'appflowy_to_supabase': appflowy_stats,
            'supabase_to_appflowy': supabase_stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in bidirectional sync: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    result = run_bidirectional_sync()
    print(json.dumps(result, indent=2))
