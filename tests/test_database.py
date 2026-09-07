"""
Unit Tests for PhotoPro Local Database Management
"""
import os
import tempfile
import unittest
from app.database.db import DatabaseManager
from app.config.settings import AppSettings

class TestDatabase(unittest.TestCase):
    def test_database_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_photopro.db")
            db = DatabaseManager(db_path=db_path)

            # 1. Test default settings load
            settings = db.load_settings()
            self.assertEqual(settings.default_paper, "4R")
            self.assertEqual(settings.default_photo_size, "passport")

            # 2. Test saving modified settings
            settings.default_paper = "A4"
            settings.default_copies = 12
            settings.retouch_strength = 65
            self.assertTrue(db.save_settings(settings))

            # Reload and verify
            reloaded = db.load_settings()
            self.assertEqual(reloaded.default_paper, "A4")
            self.assertEqual(reloaded.default_copies, 12)
            self.assertEqual(reloaded.retouch_strength, 65)

            # 3. Test Print History Logging
            self.assertTrue(db.log_print_job(
                photo_name="customer_photo.jpg",
                paper_size="4R",
                photo_size="passport",
                copies=8,
                status="completed"
            ))

            history = db.get_print_history()
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["photo_name"], "customer_photo.jpg")
            self.assertEqual(history[0]["copies"], 8)

            # 4. Test Background Presets
            presets = db.get_background_presets()
            self.assertTrue(len(presets) >= 3)
            preset_names = [p["name"] for p in presets]
            self.assertIn("Studio White", preset_names)
            self.assertIn("Passport Blue", preset_names)

    def test_corrupt_database_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "corrupt_test.db")
            # Write corrupted garbage data
            with open(db_path, "wb") as f:
                f.write(b"NOT_A_SQLITE_DATABASE_CORRUPTED_BYTES")

            # DatabaseManager should auto-detect and safely re-initialize
            db = DatabaseManager(db_path=db_path)
            settings = db.load_settings()
            self.assertIsNotNone(settings)
            self.assertEqual(settings.default_paper, "4R")

if __name__ == "__main__":
    unittest.main()
