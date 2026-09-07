"""
PhotoPro Intelligent Portrait Enhancement & Conservative Skin Retouching
Performs subtle blemish reduction, facial exposure compensation, skin tone balancing,
histogram contrast stretching, and unsharp mask sharpening.
Preserves natural identity, pores, and facial structure (never plastic or fake).
"""
from __future__ import annotations
import logging
from typing import Tuple, Optional
try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)

class PhotoEnhancer:
    """Professional portrait photo enhancement engine."""

    def __init__(self):
        pass

    def detect_skin_mask(self, image_rgb: np.ndarray) -> Tuple[np.ndarray, float, float, float]:
        """
        Computes continuous skin probability mask using YCbCr color distribution.
        Returns: (soft_skin_mask, avg_y, avg_cb, avg_cr)
        """
        h, w = image_rgb.shape[:2]
        img_float = image_rgb.astype(np.float32)

        # Standard ITU-R BT.601 conversion
        r = img_float[:, :, 0]
        g = img_float[:, :, 1]
        b = img_float[:, :, 2]

        y  = 0.299 * r + 0.587 * g + 0.114 * b
        cb = 128.0 - 0.168736 * r - 0.331264 * g + 0.5 * b
        cr = 128.0 + 0.5 * r - 0.418688 * g - 0.081312 * b

        # Human skin locus across ethnicities
        skin_condition = (
            (y > 38.0) & (y < 225.0) &
            (r > g) & (g > b * 0.70) &
            (cb >= 75.0) & (cb <= 135.0) &
            (cr >= 130.0) & (cr <= 180.0) &
            ((cr - cb) > 8.0)
        )

        skin_prob = np.zeros((h, w), dtype=np.float32)
        skin_prob[skin_condition] = 1.0

        # Taper boundaries to avoid harsh transitions
        dark_falloff = np.clip((y - 38.0) / 17.0, 0.0, 1.0)
        bright_falloff = np.clip((225.0 - y) / 15.0, 0.0, 1.0)
        chroma_falloff = np.clip((cr - cb - 8.0) / 6.0, 0.0, 1.0)

        skin_prob *= dark_falloff * bright_falloff * chroma_falloff

        # Measure statistics on skin region
        skin_pixels = skin_prob > 0.3
        if np.count_nonzero(skin_pixels) > 50:
            avg_y = float(np.mean(y[skin_pixels]))
            avg_cb = float(np.mean(cb[skin_pixels]))
            avg_cr = float(np.mean(cr[skin_pixels]))
        else:
            avg_y, avg_cb, avg_cr = 128.0, 105.0, 148.0

        # Gentle Gaussian smoothing for feathering
        try:
            import cv2
            soft_skin = cv2.GaussianBlur(skin_prob, (7, 7), 1.5)
        except Exception:
            soft_skin = skin_prob

        return soft_skin, avg_y, avg_cb, avg_cr

    def reduce_blemishes(
        self,
        image_rgb: np.ndarray,
        soft_skin: np.ndarray,
        retouch_strength: float = 0.50
    ) -> np.ndarray:
        """
        Conservative blemish & pimple reduction.
        Detects localized dark spots and red inflammatory anomalies on skin,
        gently blending them with surrounding skin tone while preserving
        permanent facial features, beard, moustache, eyes, and pores.
        """
        if retouch_strength <= 0.01:
            return image_rgb

        h, w = image_rgb.shape[:2]
        try:
            import cv2
            # Bilateral filter retains sharp edges while smoothing minor texture
            bilateral = cv2.bilateralFilter(image_rgb, d=7, sigmaColor=35, sigmaSpace=7)
            # High-pass difference: highlights localized spots and pimples
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
            blur_gray = cv2.cvtColor(bilateral, cv2.COLOR_RGB2GRAY).astype(np.float32)
            diff = blur_gray - gray  # positive where spot is darker than surrounding

            # Red anomaly on skin
            r = image_rgb[:, :, 0].astype(np.float32)
            g = image_rgb[:, :, 1].astype(np.float32)
            br = bilateral[:, :, 0].astype(np.float32)
            bg = bilateral[:, :, 1].astype(np.float32)
            red_anomaly = (r - g) - (br - bg)

            # Blemish score
            blemish_score = np.zeros((h, w), dtype=np.float32)
            dark_mask = (diff > 5.0) & (diff < 40.0)
            blemish_score[dark_mask] += (diff[dark_mask] - 5.0) / 25.0

            red_mask = (red_anomaly > 7.0) & (red_anomaly < 45.0)
            blemish_score[red_mask] += (red_anomaly[red_mask] - 7.0) / 25.0

            # Compute blend map: only on skin regions
            blend_map = (
                (0.12 * retouch_strength + np.clip(blemish_score * 0.55 * retouch_strength, 0.0, 0.65))
                * soft_skin
            )
            blend_map = np.clip(blend_map, 0.0, 0.70)  # Max 70% to never look fake/plastic
            blend_3d = np.repeat(blend_map[:, :, np.newaxis], 3, axis=2)

            out = image_rgb.astype(np.float32) * (1.0 - blend_3d) + bilateral.astype(np.float32) * blend_3d
            return np.clip(out, 0, 255).astype(np.uint8)
        except Exception as e:
            logger.warning(f"Blemish reduction fallback: {e}")
            return image_rgb

    def lift_face_brightness(
        self,
        image_rgb: np.ndarray,
        soft_skin: np.ndarray,
        avg_y: float
    ) -> np.ndarray:
        """
        Intelligently lifts exposure on underexposed faces without washing out highlights.
        """
        # Determine necessary brightness lift based on skin luminance
        if avg_y < 115.0:
            lift_amount = min(22.0, (115.0 - avg_y) * 0.38)
        elif avg_y < 145.0:
            lift_amount = min(8.0, (145.0 - avg_y) * 0.12)
        else:
            return image_rgb  # Well-exposed or high-key portrait

        img_float = image_rgb.astype(np.float32)
        # Highlight protection factor (approaches 0 near 245)
        lum = 0.299 * img_float[:, :, 0] + 0.587 * img_float[:, :, 1] + 0.114 * img_float[:, :, 2]
        protect = np.clip((245.0 - lum) / 100.0, 0.0, 1.0)

        lift_map = lift_amount * soft_skin * protect
        lift_3d = np.repeat(lift_map[:, :, np.newaxis], 3, axis=2)

        out = img_float + lift_3d
        return np.clip(out, 0, 255).astype(np.uint8)

    def balance_skin_tone(
        self,
        image_rgb: np.ndarray,
        soft_skin: np.ndarray,
        avg_cb: float,
        avg_cr: float
    ) -> np.ndarray:
        """
        Subtly corrects unnatural color casts (e.g. green fluorescent or heavy yellow tint)
        towards natural healthy portrait skin tones.
        """
        # Target canonical studio skin chroma
        target_cb = 106.0
        target_cr = 148.0
        cb_shift = (target_cb - avg_cb) * 0.15
        cr_shift = (target_cr - avg_cr) * 0.15

        if abs(cb_shift) < 0.8 and abs(cr_shift) < 0.8:
            return image_rgb

        img_float = image_rgb.astype(np.float32)
        dr = (1.402 * cr_shift) * soft_skin
        dg = (-0.344136 * cb_shift - 0.714136 * cr_shift) * soft_skin
        db = (1.772 * cb_shift) * soft_skin

        out = img_float.copy()
        out[:, :, 0] += dr
        out[:, :, 1] += dg
        out[:, :, 2] += db
        return np.clip(out, 0, 255).astype(np.uint8)

    def color_grade_and_contrast(self, image_rgb: np.ndarray) -> np.ndarray:
        """
        Applies professional histogram contrast stretching (1st-99th percentile)
        and a subtle 4% natural vibrancy boost.
        """
        h, w = image_rgb.shape[:2]
        # Sample center region to avoid edge background influences
        crop_y0, crop_y1 = int(h * 0.10), int(h * 0.90)
        crop_x0, crop_x1 = int(w * 0.10), int(w * 0.90)
        center_zone = image_rgb[crop_y0:crop_y1, crop_x0:crop_x1]

        gray = (
            center_zone[:, :, 0].astype(np.float32) * 0.299 +
            center_zone[:, :, 1].astype(np.float32) * 0.587 +
            center_zone[:, :, 2].astype(np.float32) * 0.114
        )
        p_lo = float(np.percentile(gray, 1.0))
        p_hi = float(np.percentile(gray, 99.0))

        # Safe bounds to prevent clipping
        lo = min(p_lo, 32.0)
        hi = max(p_hi, 228.0)

        img_float = image_rgb.astype(np.float32)
        if hi > lo + 10.0:
            stretched = (img_float - lo) * (255.0 / (hi - lo))
        else:
            stretched = img_float

        # Subtle 4% vibrancy
        lum = (
            0.299 * stretched[:, :, 0] +
            0.587 * stretched[:, :, 1] +
            0.114 * stretched[:, :, 2]
        )[:, :, np.newaxis]
        sat_boost = lum + (stretched - lum) * 1.04

        return np.clip(sat_boost, 0, 255).astype(np.uint8)

    def unsharp_mask(
        self,
        image_rgb: np.ndarray,
        amount: float = 0.35,
        radius: float = 1.0,
        threshold: float = 4.0
    ) -> np.ndarray:
        """
        High-precision unsharp masking for crisp eye, hair, and clothing details
        without amplifying skin grain or haloing.
        """
        try:
            import cv2
            blurred = cv2.GaussianBlur(image_rgb, (0, 0), radius)
            diff = image_rgb.astype(np.float32) - blurred.astype(np.float32)

            # Apply threshold to avoid sharpening minor noise
            mask = np.abs(diff) >= threshold
            sharpened = image_rgb.astype(np.float32) + diff * amount * mask

            return np.clip(sharpened, 0, 255).astype(np.uint8)
        except Exception:
            return image_rgb

    def apply_manual_fine_tune(
        self,
        image_rgb: np.ndarray,
        brightness: int = 0,
        contrast: int = 0,
        saturation: int = 0
    ) -> np.ndarray:
        """
        Optional fine-tuning controls (-40 to +40).
        """
        if brightness == 0 and contrast == 0 and saturation == 0:
            return image_rgb

        img_float = image_rgb.astype(np.float32)
        c_factor = (100.0 + contrast) / 100.0
        s_factor = (100.0 + saturation) / 100.0

        # Brightness & Contrast
        adjusted = (img_float + brightness - 128.0) * c_factor + 128.0

        # Saturation
        lum = (
            0.299 * adjusted[:, :, 0] +
            0.587 * adjusted[:, :, 1] +
            0.114 * adjusted[:, :, 2]
        )[:, :, np.newaxis]
        adjusted = lum + (adjusted - lum) * s_factor

        return np.clip(adjusted, 0, 255).astype(np.uint8)

    def enhance_full_pipeline(
        self,
        image_rgb: np.ndarray,
        auto_skin_retouch: bool = True,
        retouch_strength: int = 50,
        auto_brightness: bool = True,
        auto_color_grading: bool = True,
        auto_sharpen: bool = True,
        manual_brightness: int = 0,
        manual_contrast: int = 0,
        manual_saturation: int = 0
    ) -> np.ndarray:
        """
        Executes the full automated portrait enhancement pipeline.
        """
        result = image_rgb.copy()

        # 1. Skin & Facial Analysis
        soft_skin, avg_y, avg_cb, avg_cr = self.detect_skin_mask(result)

        # 2. Conservative blemish reduction & skin smoothing
        if auto_skin_retouch:
            strength_float = max(0.0, min(1.0, retouch_strength / 100.0))
            result = self.reduce_blemishes(result, soft_skin, strength_float)

        # 3. Adaptive face brightness compensation
        if auto_brightness:
            result = self.lift_face_brightness(result, soft_skin, avg_y)

        # 4. Subtle skin tone balancing
        result = self.balance_skin_tone(result, soft_skin, avg_cb, avg_cr)

        # 5. Contrast stretching and natural color grading
        if auto_color_grading:
            result = self.color_grade_and_contrast(result)

        # 6. Unsharp mask detail enhancement
        if auto_sharpen:
            result = self.unsharp_mask(result)

        # 7. Manual fine-tune overrides if adjusted by user
        result = self.apply_manual_fine_tune(
            result, manual_brightness, manual_contrast, manual_saturation
        )

        return result
