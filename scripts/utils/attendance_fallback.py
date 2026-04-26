"""
Attendance fallback logger.

When Supabase is unavailable, we still want check-ins to be recorded locally so
the demo can run end-to-end without external services.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytz

from config.settings import APPFLOWY_EXPORT_PATH, LOG_FILE_PATH, TIMEZONE
from scripts.utils.logger import logger


ATTENDANCE_FALLBACK_FILE = LOG_FILE_PATH / "attendance_fallback.jsonl"


def _now_iso() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).isoformat()


def append_check_in(shift_id: str, user_id: str, method: str) -> dict:
    """
    Append a check-in record to a local JSONL file.

    Returns the record written.
    """
    record = {
        "timestamp": _now_iso(),
        "shift_id": str(shift_id),
        "user_id": str(user_id),
        "method": str(method),
        "source": "local_fallback",
    }

    try:
        ATTENDANCE_FALLBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ATTENDANCE_FALLBACK_FILE, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
        return record
    except Exception as e:
        logger.error(f"Failed to write attendance fallback log: {e}")
        raise


def _load_volunteer_lookup() -> dict:
    volunteers_file = Path(APPFLOWY_EXPORT_PATH) / "volunteers.json"
    if not volunteers_file.exists():
        return {}

    try:
        with open(volunteers_file, encoding="utf-8") as f:
            volunteers = json.load(f)
        return {str(v.get("id")): v for v in volunteers if v.get("id")}
    except Exception as e:
        logger.warning(f"Could not load volunteers.json for attendance fallback: {e}")
        return {}


def read_shift_attendance(shift_id: str) -> dict:
    """
    Summarize fallback attendance for a shift.

    Returns a structure compatible with the API response used by the UI.
    """
    shift_id = str(shift_id)
    if not ATTENDANCE_FALLBACK_FILE.exists():
        return {
            "total_assigned": 0,
            "checked_in": 0,
            "not_checked_in": 0,
            "volunteers": [],
            "source": "local_fallback",
        }

    records = []
    try:
        with open(ATTENDANCE_FALLBACK_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(rec.get("shift_id")) == shift_id:
                    records.append(rec)
    except Exception as e:
        logger.warning(f"Could not read attendance fallback log: {e}")
        records = []

    # Latest record per user_id wins.
    latest_by_user = {}
    for rec in records:
        user_id = str(rec.get("user_id"))
        latest_by_user[user_id] = rec

    volunteer_lookup = _load_volunteer_lookup()
    volunteers = []
    for user_id, rec in latest_by_user.items():
        vol = volunteer_lookup.get(user_id, {})
        volunteers.append(
            {
                "name": vol.get("name") or user_id,
                "email": vol.get("email", ""),
                "checked_in": True,
                "check_in_time": rec.get("timestamp"),
                "user_id": user_id,
            }
        )

    volunteers.sort(key=lambda v: (v.get("name") or "").lower())
    checked_in = len(volunteers)

    return {
        "total_assigned": checked_in,
        "checked_in": checked_in,
        "not_checked_in": 0,
        "volunteers": volunteers,
        "source": "local_fallback",
    }

