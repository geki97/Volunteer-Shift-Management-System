import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import config.settings as settings
import scripts.check_status as check_status
import scripts.data_sync_daemon as data_sync_daemon
from scripts.utils import logger as logger_module
from scripts.utils.database import SupabaseManager


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestRuntimeImport(unittest.TestCase):
    def test_web_app_imports_cleanly(self):
        result = subprocess.run(
            [sys.executable, "-c", "import web.check_in_app; print('IMPORT_OK')"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Import failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        self.assertIn("IMPORT_OK", result.stdout)


class TestHealthReporting(unittest.TestCase):
    @patch("scripts.check_status.Path")
    def test_check_status_does_not_report_healthy_when_database_health_fails(self, path_cls):
        volunteers_file = MagicMock()
        volunteers_file.exists.return_value = True
        volunteers_file.stat.return_value.st_size = 1024

        shifts_file = MagicMock()
        shifts_file.exists.return_value = True
        shifts_file.stat.return_value.st_size = 2048

        log_file = MagicMock()
        log_file.name = "volunteer_system.log"
        log_file.stat.return_value.st_mtime = 1

        path_cls.side_effect = lambda value="": volunteers_file if "volunteers" in str(value) else shifts_file

        fake_log_path = MagicMock()
        fake_log_path.glob.return_value = [log_file]

        with patch("builtins.open", unittest.mock.mock_open(read_data="[]")):
            with patch.object(check_status, "LOG_FILE_PATH", fake_log_path):
                with patch.object(
                    check_status.db,
                    "check_connection_status",
                    return_value=(False, {"error": "dns failure"}),
                    create=True,
                ):
                    report = check_status.check_system_status()

        self.assertEqual(report["system_health"], "PARTIAL")
        self.assertTrue(
            any("dns failure" in issue.lower() for issue in report["issues"]),
            msg=f"Expected database failure to be surfaced, got: {report['issues']}",
        )


class TestSyncMapping(unittest.TestCase):
    def test_sync_volunteers_uses_export_id_as_appflowy_id(self):
        sample_volunteers = [
            {
                "id": "vol_123",
                "name": "Volunteer One",
                "email": "vol@example.com",
                "phone": "123",
                "skills": ["Food Prep"],
                "availability": ["Monday"],
                "status": "Active",
                "notes": "",
            }
        ]

        with patch.object(data_sync_daemon, "load_appflowy_exports", return_value=(sample_volunteers, [])):
            with patch.object(data_sync_daemon.db, "get_volunteer_by_appflowy_id", return_value=None) as get_existing:
                with patch.object(data_sync_daemon.db, "create_volunteer") as create_volunteer:
                    synced = data_sync_daemon.sync_volunteers()

        self.assertEqual(synced, 1)
        get_existing.assert_called_once_with("vol_123")
        create_payload = create_volunteer.call_args.args[0]
        self.assertEqual(create_payload["appflowy_id"], "vol_123")

    def test_sync_shifts_uses_export_id_as_appflowy_id(self):
        sample_shifts = [
            {
                "id": "shift_123",
                "shift_name": "Morning Shift",
                "shift_date": "2026-04-18T09:00:00",
                "end_time": "12:00",
                "location": "Warehouse",
                "required_volunteers": 4,
                "status": "Open",
                "priority": "Medium",
                "shift_coordinator": "vol_123",
                "special_instructions": "",
            }
        ]

        with patch.object(data_sync_daemon, "load_appflowy_exports", return_value=([], sample_shifts)):
            with patch.object(data_sync_daemon.db, "get_shift_by_appflowy_id", return_value=None) as get_existing:
                with patch.object(data_sync_daemon.db, "create_shift") as create_shift:
                    synced = data_sync_daemon.sync_shifts()

        self.assertEqual(synced, 1)
        get_existing.assert_called_once_with("shift_123")
        create_payload = create_shift.call_args.args[0]
        self.assertEqual(create_payload["appflowy_id"], "shift_123")


class TestStartupIntegrity(unittest.TestCase):
    def test_startup_script_only_references_existing_python_files(self):
        script_path = PROJECT_ROOT / "start_automation.bat"
        lines = script_path.read_text(encoding="utf-8", errors="replace").splitlines()

        referenced = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line.lower().startswith("python "):
                continue

            script_ref = line.split()[1].replace("\\", "/")
            if script_ref.startswith("scripts/") or script_ref.endswith(".py"):
                referenced.append(script_ref)

        missing = [ref for ref in referenced if not (PROJECT_ROOT / ref).exists()]
        self.assertEqual(
            missing,
            [],
            msg=f"Startup script references missing Python files: {missing}",
        )


class TestConfigValidation(unittest.TestCase):
    def test_validate_config_rejects_placeholder_supabase_values(self):
        with patch.object(settings, "SUPABASE_URL", "https://your-project.supabase.co"):
            with patch.object(settings, "SUPABASE_KEY", "your_supabase_anon_key"):
                with patch.object(settings, "SENDGRID_API_KEY", "sg.fake"):
                    with patch.object(settings, "SENDGRID_FROM_EMAIL", "test@example.com"):
                        with patch.object(settings, "TWILIO_ACCOUNT_SID", "AC1234567890"):
                            with patch.object(settings, "TWILIO_AUTH_TOKEN", "token"):
                                with patch.object(settings, "FLASK_DEBUG", False):
                                    with patch.object(settings, "FLASK_SECRET_KEY", "x" * 32):
                                        with patch.object(settings, "QR_SIGNING_KEY", b"strong-signing-key-1234567890"):
                                            errors = settings.validate_config()

        self.assertTrue(
            any("placeholder" in error.lower() for error in errors),
            msg=f"Expected placeholder warning, got: {errors}",
        )


class TestDatabaseHealthCheck(unittest.TestCase):
    def test_check_connection_status_surfaces_query_failures(self):
        manager = SupabaseManager.__new__(SupabaseManager)

        execute = MagicMock(side_effect=OSError("dns failure"))
        limit = MagicMock(return_value=MagicMock(execute=execute))
        select = MagicMock(return_value=MagicMock(limit=limit))
        table = MagicMock(return_value=MagicMock(select=select))
        manager.client = MagicMock(table=table)

        is_healthy, details = manager.check_connection_status()

        self.assertFalse(is_healthy)
        self.assertIn("dns failure", details["error"].lower())


class TestReportSafeClaims(unittest.TestCase):
    def test_demo_script_does_not_overclaim_unsupported_features(self):
        demo_source = (PROJECT_ROOT / "full_demo.py").read_text(encoding="utf-8", errors="replace")

        self.assertNotIn("Skills Matching", demo_source)
        self.assertNotIn("ready for full deployment", demo_source.lower())

    def test_env_template_uses_obvious_placeholders(self):
        template = (PROJECT_ROOT / ".env.template").read_text(encoding="utf-8", errors="replace")

        self.assertIn("your_twilio_account_sid_here", template)
        self.assertIn("your_twilio_auth_token_here", template)
        self.assertIn("your_twilio_phone_number_here", template)


class TestLegacyHelperScripts(unittest.TestCase):
    def test_helper_scripts_do_not_execute_on_import(self):
        result = subprocess.run(
            [sys.executable, "-c", "import test_data, test_status; print('IMPORTED')"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "IMPORTED")

    def test_legacy_status_helper_does_not_claim_healthy_on_backend_failure(self):
        result = subprocess.run(
            [sys.executable, "test_status.py"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("SYSTEM STATUS: HEALTHY", result.stdout)


class _Cp1252Stream:
    encoding = "cp1252"

    def __init__(self):
        self.buffer = []

    def write(self, data):
        encoded = data.encode(self.encoding, errors="strict")
        self.buffer.append(encoded.decode(self.encoding))

    def flush(self):
        return None


class TestLoggerConsoleSafety(unittest.TestCase):
    def test_safe_console_handler_replaces_unencodable_characters(self):
        stream = _Cp1252Stream()
        handler = logger_module.SafeConsoleHandler(stream=stream)
        handler.setFormatter(logger_module.logging.Formatter("%(message)s"))

        record = logger_module.logging.LogRecord(
            name="test",
            level=logger_module.logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="✅ Sync complete",
            args=(),
            exc_info=None,
        )

        handler.emit(record)

        output = "".join(stream.buffer)
        self.assertIn("? Sync complete", output)


class TestLoggerFileEncoding(unittest.TestCase):
    def test_setup_logger_uses_utf8_for_log_files(self):
        log_filename = "utf8_test.log"
        with patch.object(logger_module, "LOG_FILE_PATH", PROJECT_ROOT / "logs"):
            temp_logger = logger_module.setup_logger("utf8_test_logger", log_file=log_filename)

        try:
            file_handlers = [
                handler for handler in temp_logger.handlers
                if isinstance(handler, logger_module.logging.FileHandler)
            ]
            self.assertTrue(file_handlers, msg="Expected a file handler to be configured")
            self.assertEqual((file_handlers[0].encoding or "").lower(), "utf-8")
        finally:
            for handler in temp_logger.handlers:
                handler.close()
            log_path = PROJECT_ROOT / "logs" / log_filename
            if log_path.exists():
                log_path.unlink()


if __name__ == "__main__":
    unittest.main()
