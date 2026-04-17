from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY, TIMEZONE
from scripts.utils.logger import logger
from datetime import datetime, timedelta
import json
import pytz

class SupabaseManager:
    """Manage all Supabase database operations"""
    
    def __init__(self):
        try:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("[OK] Connected to Supabase")
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Supabase: {e}")
            raise
    
    # VOLUNTEER OPERATIONS
    def create_volunteer(self, volunteer_data):
        """Create a new volunteer in Supabase"""
        try:
            result = self.client.table('volunteers').insert(volunteer_data).execute()
            logger.info(f"Created volunteer: {volunteer_data.get('name')}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating volunteer: {e}")
            return None
    
    def get_volunteer_by_appflowy_id(self, appflowy_id):
        """Get volunteer by their AppFlowy ID"""
        try:
            result = self.client.table('volunteers')\
                .select('*')\
                .eq('appflowy_id', appflowy_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching volunteer: {e}")
            return None
    
    def update_volunteer(self, appflowy_id, updates):
        """Update volunteer data"""
        try:
            result = self.client.table('volunteers')\
                .update(updates)\
                .eq('appflowy_id', appflowy_id)\
                .execute()
            logger.info(f"Updated volunteer: {appflowy_id}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating volunteer: {e}")
            return None
    
    def get_all_volunteers(self, status='Active'):
        """Get all volunteers with optional status filter"""
        try:
            query = self.client.table('volunteers').select('*')
            if status:
                query = query.eq('status', status)
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching volunteers: {e}")
            return []
    
    # SHIFT OPERATIONS
    def create_shift(self, shift_data):
        """Create a new shift in Supabase"""
        try:
            result = self.client.table('shifts').insert(shift_data).execute()
            logger.info(f"Created shift: {shift_data.get('shift_name')}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating shift: {e}")
            return None
    
    def get_shift_by_appflowy_id(self, appflowy_id):
        """Get shift by AppFlowy ID"""
        try:
            result = self.client.table('shifts')\
                .select('*')\
                .eq('appflowy_id', appflowy_id)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error fetching shift: {e}")
            return None
    
    def get_upcoming_shifts(self, hours_ahead=24):
        """Get shifts happening in the next X hours"""
        try:
            tz = pytz.timezone(TIMEZONE)
            now = datetime.now(tz)
            future = now + timedelta(hours=hours_ahead)
            
            result = self.client.table('shifts')\
                .select('*')\
                .gte('shift_date', now.isoformat())\
                .lte('shift_date', future.isoformat())\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching upcoming shifts: {e}")
            return []
    
    def get_all_shifts(self, status=None):
        """Get all shifts with optional status filter"""
        try:
            query = self.client.table('shifts').select('*')
            if status:
                query = query.eq('status', status)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching all shifts: {e}")
            return []

    def check_connection_status(self):
        """Run a lightweight health check without masking query failures."""
        try:
            volunteers_result = (
                self.client.table('volunteers')
                .select('*', count='exact')
                .limit(1)
                .execute()
            )
            shifts_result = (
                self.client.table('shifts')
                .select('*', count='exact')
                .limit(1)
                .execute()
            )

            volunteers_count = getattr(volunteers_result, 'count', None)
            if volunteers_count is None:
                volunteers_count = len(volunteers_result.data or [])

            shifts_count = getattr(shifts_result, 'count', None)
            if shifts_count is None:
                shifts_count = len(shifts_result.data or [])

            return True, {
                'volunteers_count': volunteers_count,
                'shifts_count': shifts_count,
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False, {'error': str(e)}
    
    # ASSIGNMENT OPERATIONS
    def create_assignment(self, shift_id, volunteer_id):
        """Create shift assignment"""
        try:
            assignment_data = {
                'shift_id': shift_id,
                'volunteer_id': volunteer_id,
                'assigned_date': datetime.now().isoformat()
            }
            result = self.client.table('shift_assignments').insert(assignment_data).execute()
            logger.info(f"Created assignment: volunteer {volunteer_id} to shift {shift_id}")
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating assignment: {e}")
            return None
    
    def get_shift_assignments(self, shift_id):
        """Get all volunteers assigned to a shift"""
        try:
            result = self.client.table('shift_assignments')\
                .select('*, volunteers(*)')\
                .eq('shift_id', shift_id)\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching shift assignments: {e}")
            return []
    
    def mark_checked_in(self, shift_id, volunteer_id):
        """Mark volunteer as checked in for shift"""
        try:
            # First try to update existing assignment
            result = self.client.table('shift_assignments')\
                .update({
                    'checked_in': True,
                    'check_in_time': datetime.now().isoformat()
                })\
                .eq('shift_id', shift_id)\
                .eq('volunteer_id', volunteer_id)\
                .execute()
            
            # If update found records, return the result
            if result.data:
                logger.info(f"[+] Marked volunteer {volunteer_id} as checked in for shift {shift_id}")
                return result.data[0]
            
            # If no records found, create a new assignment record
            new_assignment = {
                'shift_id': shift_id,
                'volunteer_id': volunteer_id,
                'checked_in': True,
                'check_in_time': datetime.now().isoformat(),
                'assigned_date': datetime.now().isoformat()
            }
            create_result = self.client.table('shift_assignments').insert(new_assignment).execute()
            
            if create_result.data:
                logger.info(f"[+] Created and checked in volunteer {volunteer_id} for shift {shift_id}")
                return create_result.data[0]
            else:
                logger.warning(f"[!] Could not create assignment for volunteer {volunteer_id}")
                return None
                
        except Exception as e:
            logger.error(f"[!] Error marking check-in: {e}")
            return None
    
    # LOGGING OPERATIONS
    def log_notification(self, notification_type, recipient_id, shift_id, status, message_id=None, error=None):
        """Log notification attempt"""
        try:
            log_data = {
                'notification_type': notification_type,
                'recipient_id': recipient_id,
                'shift_id': shift_id,
                'status': status,
                'message_id': message_id,
                'error_message': error
            }
            self.client.table('notification_log').insert(log_data).execute()
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    def log_audit(self, entity_type, entity_id, action, changed_fields, performed_by='system'):
        """Log audit trail"""
        try:
            audit_data = {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'action': action,
                'changed_fields': json.dumps(changed_fields),
                'performed_by': performed_by
            }
            self.client.table('audit_log').insert(audit_data).execute()
        except Exception as e:
            logger.error(f"Error logging audit: {e}")

# Create singleton instance
db = SupabaseManager()
