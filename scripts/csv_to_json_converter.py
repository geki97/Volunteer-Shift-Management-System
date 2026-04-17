"""
CSV to JSON Converter for AppFlowy Exports
Converts AppFlowy CSV exports to JSON format for syncing
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.logger import setup_logger
from config.settings import APPFLOWY_EXPORT_PATH

logger = setup_logger('csv_to_json_converter')


def csv_to_json(csv_file, json_file, record_type):
    """
    Convert AppFlowy CSV export to JSON format
    
    Args:
        csv_file: Path to CSV file exported from AppFlowy
        json_file: Path where JSON file should be saved
        record_type: 'volunteers' or 'shifts'
    
    Returns:
        List of converted records
    """
    
    records = []
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        logger.warning(f"⚠️  CSV file not found: {csv_file}")
        return records
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if record_type == 'volunteers':
                    # Parse multi-select fields (comma-separated become lists)
                    skills = []
                    if row.get('Skills'):
                        skills = [s.strip() for s in row.get('Skills', '').split(',')]
                    
                    availability = []
                    if row.get('Availability'):
                        availability = [a.strip() for a in row.get('Availability', '').split(',')]
                    
                    record = {
                        'id': row.get('Name', '').lower().replace(' ', '_'),
                        'name': row.get('Name', ''),
                        'email': row.get('Email', ''),
                        'phone': row.get('Phone Number ', '').strip() or row.get('Phone', ''),
                        'skills': skills,
                        'availability': availability,
                        'total_shifts_assigned': int(row.get('Total Shifts', 0) or 0),
                        'shifts_completed': int(row.get('Attended Shifts', 0) or 0),
                        'no_shows': int(row.get('Missed Shift', 0) or 0),
                        'cancellations': 0,
                        'reliability_score': float(row.get('Reliability Score', 0) or 0),
                        'status': row.get('Status', 'Active'),
                        'date_registered': row.get('Join Date', ''),
                        'notes': ''
                    }
                
                elif record_type == 'shifts':
                    # Parse multi-select fields
                    assigned_volunteers = []
                    if row.get('Asigned Volunteers'):
                        assigned_volunteers = [v.strip() for v in row.get('Asigned Volunteers', '').split(',')]
                    
                    # Combine date and time
                    shift_datetime = f"{row.get('Date', '')} {row.get('Start Time', '')}"
                    
                    record = {
                        'id': row.get('Shift Name', '').lower().replace(' ', '_'),
                        'shift_name': row.get('Shift Name', ''),
                        'shift_date': shift_datetime,
                        'end_time': row.get('End Time', ''),
                        'location': row.get('Location', ''),
                        'required_volunteers': int(row.get('Required Volunteers', 0) or 0),
                        'current_assigned': int(row.get('Current Coverage', 0) or 0),
                        'status': row.get('Status', 'Open'),
                        'priority': 'High' if row.get('Shift type', '') == 'Food Distribution' else 'Medium',
                        'volunteer_roles': [row.get('Shift type', '')],
                        'assigned_volunteers': assigned_volunteers,
                        'shift_coordinator': row.get('Lead Coordinator', ''),
                        'special_instructions': row.get('Description', ''),
                        'created_date': row.get('Date', '')
                    }
                
                else:
                    logger.warning(f"⚠️  Unknown record type: {record_type}")
                    continue
                
                records.append(record)
        
        # Write JSON file
        json_path = Path(json_file)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Converted {len(records)} {record_type} to JSON")
        logger.info(f"   📄 Saved to: {json_file}")
        
        return records
        
    except Exception as e:
        logger.error(f"❌ Error converting {record_type}: {e}")
        return records


def convert_appflowy_exports():
    """
    Convert all AppFlowy CSV exports to JSON
    Looks for volunteers.csv and shifts.csv in appflowy_exports/
    """
    
    logger.info("="*60)
    logger.info("🔄 Starting AppFlowy CSV → JSON Conversion")
    logger.info("="*60)
    
    export_path = APPFLOWY_EXPORT_PATH
    
    # Convert volunteers - look for real data file
    volunteers_csv = Path('Active_Volunteers.csv')
    if not volunteers_csv.exists():
        volunteers_csv = export_path / 'Active_Volunteers.csv'
    
    volunteers_json = export_path / 'volunteers.json'
    
    volunteers_count = 0
    if volunteers_csv.exists():
        volunteers = csv_to_json(volunteers_csv, volunteers_json, 'volunteers')
        volunteers_count = len(volunteers)
    else:
        logger.warning(f"⚠️  Not found: {volunteers_csv}")
    
    # Convert shifts - look for real data file
    shifts_csv = Path('Shifts.csv')
    if not shifts_csv.exists():
        shifts_csv = export_path / 'Shifts.csv'
    
    shifts_json = export_path / 'shifts.json'
    
    shifts_count = 0
    if shifts_csv.exists():
        shifts = csv_to_json(shifts_csv, shifts_json, 'shifts')
        shifts_count = len(shifts)
    else:
        logger.warning(f"⚠️  Not found: {shifts_csv}")
    
    logger.info("="*60)
    logger.info(f"✅ Conversion Complete")
    logger.info(f"   👥 {volunteers_count} volunteers converted")
    logger.info(f"   📋 {shifts_count} shifts converted")
    logger.info("="*60)
    
    return {
        'volunteers_count': volunteers_count,
        'shifts_count': shifts_count,
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    result = convert_appflowy_exports()
    print(json.dumps(result, indent=2))
