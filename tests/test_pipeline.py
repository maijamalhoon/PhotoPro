"""
Unit Tests for PhotoPro Biometric Crop and Enhancement Logic
"""
import unittest
from app.ai.face_detector import FaceDetector, FaceLandmarks

try:
    import numpy as np
    from app.image_processing.enhancer import PhotoEnhancer
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

class TestPipelineLogic(unittest.TestCase):
    def test_face_detector_fallback_crop(self):
        detector = FaceDetector()
        crop = detector.calculate_passport_crop(600, 600, landmarks=None)
        self.assertIsNotNone(crop)
        self.assertFalse(crop.face_detected)
        self.assertTrue(crop.crop_w > 0)
        self.assertTrue(crop.crop_h > 0)
        aspect = crop.crop_w / float(crop.crop_h)
        self.assertAlmostEqual(aspect, 35.0 / 45.0, delta=0.05)

    def test_face_landmarks_dataclass(self):
        lm = FaceLandmarks(
            bbox=(100, 100, 200, 200),
            left_eye=(150, 160),
            right_eye=(250, 160),
            roll_angle_deg=0.0
        )
        self.assertEqual(lm.bbox[0], 100)
        self.assertEqual(lm.left_eye, (150, 160))

    def test_photo_enhancer_skin_detection(self):
        if not HAVE_NUMPY:
            self.skipTest("NumPy not installed in current environment")
        enhancer = PhotoEnhancer()
        img = np.full((60, 60, 3), [215, 165, 140], dtype=np.uint8)
        soft_skin, avg_y, avg_cb, avg_cr = enhancer.detect_skin_mask(img)
        self.assertEqual(soft_skin.shape, (60, 60))
        self.assertTrue(np.mean(soft_skin) > 0.4)

if __name__ == "__main__":
    unittest.main()
