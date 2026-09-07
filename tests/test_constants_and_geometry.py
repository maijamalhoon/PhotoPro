"""
Unit Tests for PhotoPro Physical Constants & Biometric Standards
"""
import unittest
from app.config.constants import (
    DPI, MM_PER_INCH, PX_PER_MM, PAPERS, PHOTO_SIZES, MIN_GAP_MM
)

class TestConstants(unittest.TestCase):
    def test_dpi_and_scaling_ratio(self):
        self.assertEqual(DPI, 300)
        self.assertEqual(MM_PER_INCH, 25.4)
        self.assertAlmostEqual(PX_PER_MM, 300 / 25.4, places=4)

    def test_paper_formats(self):
        self.assertIn("4R", PAPERS)
        self.assertIn("A4", PAPERS)

        p_4r = PAPERS["4R"]
        self.assertEqual(p_4r.width_mm, 152.4)
        self.assertEqual(p_4r.height_mm, 101.6)
        self.assertEqual(p_4r.width_px, 1800)
        self.assertEqual(p_4r.height_px, 1200)

        p_a4 = PAPERS["A4"]
        self.assertEqual(p_a4.width_mm, 210.0)
        self.assertEqual(p_a4.height_mm, 297.0)
        self.assertTrue(abs(p_a4.width_px - 2480) <= 1)
        self.assertTrue(abs(p_a4.height_px - 3508) <= 1)

    def test_photo_formats(self):
        self.assertIn("passport", PHOTO_SIZES)
        self.assertIn("smaller", PHOTO_SIZES)

        passport = PHOTO_SIZES["passport"]
        self.assertEqual(passport.width_mm, 35.0)
        self.assertEqual(passport.height_mm, 45.0)
        self.assertTrue(abs(passport.width_px - 413) <= 1)
        self.assertTrue(abs(passport.height_px - 531) <= 1)
        self.assertAlmostEqual(passport.aspect_ratio, 35.0 / 45.0, places=4)

if __name__ == "__main__":
    unittest.main()
