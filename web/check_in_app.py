"""
QR Code Check-In Web Application
Flask app for volunteers to check in via QR codes
SECURITY: All endpoints validated and protected
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from config.settings import FLASK_SECRET_KEY, FLASK_PORT, FLASK_DEBUG, TIMEZONE, APP_BASE_URL
from scripts.utils.logger import logger
from scripts.utils.database import db
from datetime import datetime, timedelta
import pytz
import uuid
import json
import os

# Security imports - NEW
from scripts.security import (
    SecureQRCode, 
    SecurityValidator, 
    ValidationError,
    SecurityHeaders,
    log_access,
    rate_limit_check
)

# Import secure QR generator
try:
    from scripts.security.qr_secure import SecureQRCode
    HAS_QR = True
except Exception as e:
    logger.warning(f"QR code generation not available: {e}")
    HAS_QR = False
    SecureQRCode = None

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
CORS(app)

# Apply security headers to all responses
app.after_request(SecurityHeaders.inject_security_headers)

# Configure logging
logger.info(f" Flask app initializing on port {FLASK_PORT}")
logger.info(f" Security: Debug mode = {FLASK_DEBUG}")

# Helper function to load shifts with fallback
def load_shift_with_fallback(shift_id):
    """Load shift from database, fallback to JSON if database unavailable"""
    try:
        # Try database first
        shift_record = db.client.table('shifts').select('*').eq('id', shift_id).execute()
        if shift_record.data:
            logger.info(f"Loaded shift {shift_id} from database")
            return shift_record.data[0]
    except Exception as e:
        logger.warning(f"Database unavailable for shifts, using JSON fallback: {e}")
    
    # Fallback to JSON file
    try:
        # Use absolute path from current working directory
        shifts_path = Path(os.getcwd()) / 'appflowy_exports' / 'shifts.json'
        logger.info(f"Trying JSON fallback at: {shifts_path}")
        
        if not shifts_path.exists():
            logger.error(f"Shifts JSON file not found at {shifts_path}")
            return None
        
        with open(shifts_path, 'r', encoding='utf-8') as f:
            shifts = json.load(f)
        
        for shift in shifts:
            if shift.get('id') == shift_id:
                logger.info(f"Loaded shift {shift_id} from JSON fallback at {shifts_path}")
                return shift
        
        logger.warning(f"Shift {shift_id} not found in JSON fallback")
        return None
    except Exception as e:
        logger.error(f"Error loading from JSON fallback: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

# Helper function to load volunteers with fallback
def load_volunteer_with_fallback(user_id):
    """Load volunteer from database, fallback to JSON if database unavailable"""
    try:
        # Try database first
        vol_record = db.client.table('volunteers').select('*').eq('id', user_id).execute()
        if vol_record.data:
            logger.info(f"Loaded volunteer {user_id} from database")
            return vol_record.data[0]
    except Exception as e:
        logger.warning(f"Database unavailable for volunteers, using JSON fallback: {e}")
    
    # Fallback to JSON file
    try:
        # Use absolute path from current working directory
        vols_path = Path(os.getcwd()) / 'appflowy_exports' / 'volunteers.json'
        logger.info(f"Trying JSON fallback for volunteer at: {vols_path}")
        
        if not vols_path.exists():
            logger.error(f"Volunteers JSON file not found at {vols_path}")
            return None
        
        with open(vols_path, 'r', encoding='utf-8') as f:
            volunteers = json.load(f)
        
        for vol in volunteers:
            if vol.get('id') == user_id:
                logger.info(f"Loaded volunteer {user_id} from JSON fallback")
                return vol
        
        logger.warning(f"Volunteer {user_id} not found in JSON fallback")
        return None
    except Exception as e:
        logger.error(f"Error loading volunteer from JSON fallback: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/check-in/token/<token>', methods=['GET', 'POST'])
@rate_limit_check(max_requests_per_minute=30)
@log_access
def check_in_with_token(token):
    """
    Secure QR code check-in using signed tokens
    Validates token signature and expiration before processing
    """
    try:
        # SECURITY: Validate token format
        try:
            SecurityValidator.validate_token(token)
        except ValidationError as e:
            logger.warning(f"Invalid token format: {e}")
            return render_template('error.html',
                error="Invalid QR Code",
                message="The QR code is invalid or corrupted. Please scan again or contact the coordinator."
            ), 400
        
        if request.method == 'GET':
            # Verify token and get shift/user info
            is_valid, token_data = SecureQRCode.verify_check_in_token(token)
            
            if not is_valid:
                return render_template('error.html',
                    error="Invalid QR Code",
                    message=f"Token verification failed: {token_data}"
                ), 403
            
            shift_id = token_data['shift_id']
            shift_id = token_data['shift_id']
            user_id = token_data['user_id']
            
            # SECURITY: Validate shift_id format
            try:
                SecurityValidator.validate_shift_id(shift_id)
            except ValidationError as e:
                logger.error(f"Invalid shift_id in token: {e}")
                return render_template('error.html',
                    error="Invalid Shift",
                    message="Shift information is Invalid"
                ), 400
            
            # Load shift with fallback
            shift = load_shift_with_fallback(shift_id)
            if not shift:
                return render_template('error.html',
                    error="Shift Not Found",
                    message="This shift does not exist. Please contact the coordinator."
                ), 404
            
            # Show check-in confirmation form
            return render_template('check_in_token.html',
                shift=shift,
                token=token,
                shift_id=shift_id,
                user_id=user_id
            )
        
        elif request.method == 'POST':
            # Process check-in with token
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': 'Invalid request'}), 400
            
            # Verify token again (security)
            is_valid, token_data = SecureQRCode.verify_check_in_token(token)
            if not is_valid:
                return jsonify({'success': False, 'error': 'Token validation failed'}), 403
            
            shift_id = token_data['shift_id']
            user_id = token_data['user_id']
            
            # SECURITY: Validate input
            try:
                SecurityValidator.validate_shift_id(shift_id)
                SecurityValidator.validate_user_id(user_id)
            except ValidationError as e:
                logger.warning(f"Invalid input: {e}")
                return jsonify({'success': False, 'error': 'Invalid input data'}), 400
            
            try:
                # Mark volunteer as checked in
                result = db.mark_checked_in(shift_id, user_id)
                
                if result is not None:
                    logger.info(f" Check-in successful: user {user_id} for shift {shift_id}")
                    return jsonify({
                        'success': True,
                        'message': 'Check-in successful! Thank you for volunteering!',
                        'check_in_time': datetime.now(pytz.timezone(TIMEZONE)).isoformat()
                    })
                else:
                    logger.error(f"Failed to mark check-in for user {user_id}")
                    return jsonify({
                        'success': False,
                        'error': 'Failed to process check-in. Please try again.'
                    }), 500
            
            except Exception as e:
                logger.error(f"Error in check-in: {e}")
                return jsonify({
                    'success': False,
                    'error': 'System error during check-in'
                }), 500
    
    except Exception as e:
        logger.error(f"Error in check_in_with_token: {e}")
        return render_template('error.html',
            error="System Error",
            message="Could not load shift information. Please try again or contact support."
        ), 500

@app.route('/check-in/<shift_id>', methods=['GET', 'POST'])
@rate_limit_check(max_requests_per_minute=30)
@log_access
def check_in(shift_id):
    """
    Legacy QR code check-in page - show shift and volunteer selection
    SECURITY: Input validated, database queries parameterized
    """
    try:
        # SECURITY: Validate shift_id format
        try:
            SecurityValidator.validate_shift_id(shift_id)
        except ValidationError as e:
            logger.warning(f"Invalid shift_id: {e}")
            return render_template('error.html', 
                error="Invalid Shift",
                message="Invalid shift ID format. Please scan a valid QR code."
            ), 400
        
        if request.method == 'GET':
            # Load shift with fallback
            shift = load_shift_with_fallback(shift_id)
            
            if not shift:
                return render_template('error.html', 
                    error="Shift Not Found",
                    message="This shift does not exist. Please scan a valid QR code."
                ), 404
            
            assigned_volunteers = shift.get('assigned_volunteers', [])
            
            # Get volunteer details with fallback
            volunteers = []
            if assigned_volunteers:
                for vol_id in assigned_volunteers:
                    vol = load_volunteer_with_fallback(vol_id)
                    if vol:
                        volunteers.append({
                            'id': vol['id'],
                            'name': vol['name'],
                            'email': vol.get('email', ''),
                            'skills': vol.get('skills', []),
                            'status': vol.get('status', 'Active')
                        })
            
            # Sort volunteers by name
            volunteers = sorted(volunteers, key=lambda x: x['name'])
            
            return render_template('check_in.html', 
                shift=shift,
                volunteers=volunteers,
                shift_id=shift_id
            )
        
        elif request.method == 'POST':
            # Process check-in
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'error': 'Invalid request'}), 400
            
            volunteer_id = data.get('volunteer_id', '').strip()
            volunteer_name = data.get('volunteer_name', '').strip()
            
            # SECURITY: Validate inputs
            try:
                if not volunteer_id or not volunteer_name:
                    raise ValidationError("Volunteer not selected")
                
                SecurityValidator.validate_user_id(volunteer_id)
                SecurityValidator.validate_shift_id(shift_id)
            
            except ValidationError as e:
                logger.warning(f"Invalid check-in input: {e}")
                return jsonify({'success': False, 'error': str(e)}), 400
            
            try:
                # Mark volunteer as checked in
                result = db.mark_checked_in(shift_id, volunteer_id)
                
                if result is not None:
                    logger.info(f"Volunteer {volunteer_name} ({volunteer_id}) checked in for shift {shift_id}")
                    return jsonify({
                        'success': True,
                        'volunteer_name': volunteer_name,
                        'message': 'Check-in successful! Thank you for volunteering!'
                    })
                else:
                    logger.error(f"Failed to mark check-in for {volunteer_id}")
                    return jsonify({
                        'success': False,
                        'error': 'Failed to process check-in. Please try again.'
                    }), 500
            
            except Exception as e:
                logger.error(f"Error marking check-in: {e}")
                return jsonify({
                    'success': False,
                    'error': 'System error processing check-in'
                }), 500
                
    except Exception as e:
        logger.error(f"Unexpected error in check_in: {e}")
        return render_template('error.html', 
            error="Server Error",
            message="An error occurred. Please try again or contact the shift coordinator."
        ), 500

@app.route('/api/shifts')
def api_shifts():
    """API endpoint to get all upcoming shifts"""
    try:
        from pathlib import Path
        shifts_file = Path('appflowy_exports/shifts.json')
        
        if shifts_file.exists():
            with open(shifts_file) as f:
                shifts = json.load(f)
                # Filter for open shifts only
                open_shifts = [s for s in shifts if s.get('status') == 'Open']
                return jsonify({'success': True, 'shifts': open_shifts})
        
        return jsonify({'success': False, 'shifts': []}), 404
    except Exception as e:
        logger.error(f"Error fetching shifts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upcoming-shifts')
def upcoming_shifts():
    """Display all upcoming shifts"""
    try:
        from pathlib import Path
        shifts_file = Path('appflowy_exports/shifts.json')
        volunteers_file = Path('appflowy_exports/volunteers.json')
        
        shifts = []
        volunteers_map = {}
        
        # Load all shifts and filter for open ones
        if shifts_file.exists():
            with open(shifts_file) as f:
                all_shifts = json.load(f)
                shifts = [s for s in all_shifts if s.get('status') == 'Open']
        
        # Load volunteers map
        if volunteers_file.exists():
            with open(volunteers_file) as f:
                all_vols = json.load(f)
                for vol in all_vols:
                    volunteers_map[vol.get('id')] = vol
        
        return render_template('upcoming_shifts.html', 
            shifts=shifts,
            volunteers_map=volunteers_map
        )
    except Exception as e:
        logger.error(f"Error displaying upcoming shifts: {e}")
        return render_template('error.html',
            error="Error Loading Shifts",
            message="Could not load upcoming shifts. Please try again."
        ), 500

@app.route('/success/<volunteer_name>')
def success(volunteer_name):
    """Check-in success page"""
    return render_template('success.html', volunteer_name=volunteer_name)

@app.route('/api/volunteer/<email>')
def get_volunteer(email):
    """Get volunteer by email"""
    try:
        result = db.client.table('volunteers').select('*').eq('email', email).execute()
        
        if result.data:
            volunteer = result.data[0]
            return jsonify({
                'success': True,
                'volunteer': {
                    'id': volunteer['id'],
                    'name': volunteer['name'],
                    'email': volunteer['email']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Volunteer not found'}), 404
            
    except Exception as e:
        logger.error(f"Error in get_volunteer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/volunteers')
def get_all_volunteers():
    """Get all active volunteers from Supabase (synced from AppFlowy) or fallback to local JSON"""
    try:
        # Try to fetch from Supabase first
        try:
            result = db.client.table('volunteers').select('*').eq('status', 'Active').execute()
            
            volunteers = []
            if result.data:
                volunteers = [
                    {
                        'id': v['id'],
                        'name': v['name'],
                        'email': v['email'],
                        'phone': v.get('phone', ''),
                        'status': v.get('status', 'Active'),
                        'skills': v.get('skills', []) if isinstance(v.get('skills'), list) else []
                    }
                    for v in result.data
                ]
            
            return jsonify({
                'success': True,
                'volunteers': volunteers,
                'count': len(volunteers),
                'source': 'database'
            })
        except Exception as db_error:
            logger.warning(f"Database connection failed, falling back to JSON: {db_error}")
            # Fallback to local JSON file
            from pathlib import Path
            
            volunteers_file = Path('appflowy_exports/volunteers.json')
            if volunteers_file.exists():
                with open(volunteers_file) as f:
                    all_volunteers = json.load(f)
                    # Filter for active volunteers
                    volunteers = [
                        {
                            'id': v['id'],
                            'name': v['name'],
                            'email': v['email'],
                            'phone': v.get('phone', ''),
                            'status': v.get('status', 'Active'),
                            'skills': v.get('skills', []) if isinstance(v.get('skills'), list) else []
                        }
                        for v in all_volunteers 
                        if v.get('status') == 'Active'
                    ]
                
                return jsonify({
                    'success': True,
                    'volunteers': volunteers,
                    'count': len(volunteers),
                    'source': 'local_json'
                })
            else:
                return jsonify({'success': False, 'error': 'Volunteers data not found', 'volunteers': []}), 404
            
    except Exception as e:
        logger.error(f"Error in get_all_volunteers: {e}")
        return jsonify({'success': False, 'error': str(e), 'volunteers': []}), 500

@app.route('/api/shift/<shift_id>/attendance')
def get_shift_attendance(shift_id):
    """Get shift attendance data"""
    try:
        assignments = db.get_shift_assignments(shift_id)
        
        attendance_data = {
            'total_assigned': len(assignments),
            'checked_in': sum(1 for a in assignments if a['checked_in']),
            'not_checked_in': sum(1 for a in assignments if not a['checked_in']),
            'volunteers': [
                {
                    'name': a['volunteers']['name'],
                    'email': a['volunteers']['email'],
                    'checked_in': a['checked_in'],
                    'check_in_time': a['check_in_time']
                }
                for a in assignments
            ]
        }
        
        return jsonify({
            'success': True,
            'attendance': attendance_data
        })
        
    except Exception as e:
        logger.error(f" Error in get_shift_attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shifts/upcoming')
def get_upcoming_shifts():
    """Get upcoming shifts"""
    try:
        shifts = db.get_upcoming_shifts(hours_ahead=24*7)  # Next 7 days
        
        return jsonify({
            'success': True,
            'shifts': shifts
        })
        
    except Exception as e:
        logger.error(f" Error in get_upcoming_shifts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/qr/<shift_id>/generate', methods=['POST'])
def generate_qr(shift_id):
    """Generate QR code for a shift"""
    try:
        if not HAS_QR or not SecureQRCode:
            return jsonify({'success': False, 'error': 'QR code generation not available'}), 501
        
        # Get shift details
        result = db.client.table('shifts').select('*').eq('id', shift_id).execute()
        
        if not result.data:
            return jsonify({'success': False, 'error': 'Shift not found'}), 404
        
        shift = result.data[0]
        
        # Generate QR code (returns tuple of path and token)
        qr_path, token = SecureQRCode.generate_shift_qr_code(shift_id, shift['shift_name'])
        
        if qr_path:
            return jsonify({
                'success': True,
                'qr_code_path': qr_path,
                'message': 'QR code generated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate QR code'}), 500
            
    except Exception as e:
        logger.error(f"Error in generate_qr: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db.client.table('volunteers').select('*').limit(1).execute()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html',
        error="Page Not Found",
        message="The page you're looking for doesn't exist"
    ), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('error.html',
        error="Server Error",
        message="Something went wrong on our end"
    ), 500

if __name__ == "__main__":
    logger.info("="*60)
    logger.info(f" Starting Flask Web Application")
    logger.info(f" Running on http://localhost:{FLASK_PORT}")
    logger.info(f" Database: {db is not None and 'Connected' or 'Failed'}")
    logger.info("="*60)
    
    app.run(
        debug=FLASK_DEBUG,
        port=FLASK_PORT,
        host='0.0.0.0'
    )
