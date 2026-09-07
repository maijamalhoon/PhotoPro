"""
Unit Tests for PhotoPro Sheet Layout Computation & Capacity
"""
import unittest
from app.image_processing.sheet_generator import SheetGenerator
from app.config.constants import PAPERS, PHOTO_SIZES

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

class TestSheetGenerator(unittest.TestCase):
    def test_max_capacity_calculation(self):
        cap_4r_passport = SheetGenerator.calculate_max_capacity("4R", "passport")
        self.assertEqual(cap_4r_passport, 8)

        cap_a4_passport = SheetGenerator.calculate_max_capacity("A4", "passport")
        self.assertEqual(cap_a4_passport, 30)

    def test_grid_layout_math(self):
        layout = SheetGenerator.compute_grid_layout("4R", "passport", count=8)
        self.assertIsNotNone(layout)
        self.assertEqual(layout.cols, 4)
        self.assertEqual(layout.rows, 2)
        self.assertEqual(layout.count_to_place, 8)
        self.assertTrue(layout.margin_x_px >= 0)
        self.assertTrue(layout.margin_y_px >= 0)
        self.assertEqual(layout.sheet_w_px, 1800)
        self.assertEqual(layout.sheet_h_px, 1200)

    def test_render_sheet_if_numpy(self):
        if not HAVE_NUMPY:
            self.skipTest("NumPy not installed in current environment")
        passport = PHOTO_SIZES["passport"]
        test_tile = np.full((passport.height_px, passport.width_px, 3), 180, dtype=np.uint8)
        sheet, layout = SheetGenerator.render_sheet(
            test_tile,
            paper_key="4R",
            photo_size_key="passport",
            count=8,
            draw_crop_marks=True
        )
        self.assertEqual(sheet.shape, (1200, 1800, 3))

if __name__ == "__main__":
    unittest.main()
