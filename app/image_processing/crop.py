"""
PhotoPro Crop and Geometry Engine
Applies biometric crop boundaries, rotation leveling, and high-quality resampling
to exact passport photo pixel dimensions at 300 DPI.
"""
from __future__ import annotations
import math
import logging
from typing import Tuple
try:
    import numpy as np
except ImportError:
    np = None

from app.config.constants import PHOTO_SIZES, PhotoFormat

logger = logging.getLogger(__name__)

class ImageCropper:
    """Handles high-precision biometric cropping, rotation, and scaling."""

    @staticmethod
    def crop_and_resize(
        image_rgb: np.ndarray,
        crop_x: int,
        crop_y: int,
        crop_w: int,
        crop_h: int,
        rotation_angle_deg: float = 0.0,
        photo_size_key: str = "passport"
    ) -> np.ndarray:
        """
        Rotates image if required, extracts crop window, and resamples to target
        passport photo dimensions at 300 DPI (e.g. 413x531 px for 35x45mm).
        """
        target_format: PhotoFormat = PHOTO_SIZES.get(photo_size_key, PHOTO_SIZES["passport"])
        target_w = target_format.width_px
        target_h = target_format.height_px

        img_h, img_w = image_rgb.shape[:2]

        try:
            import cv2

            # 1. Apply rotation if roll angle is non-zero
            if abs(rotation_angle_deg) > 0.1:
                center_x = crop_x + crop_w / 2.0
                center_y = crop_y + crop_h / 2.0
                rot_mat = cv2.getRotationMatrix2D((center_x, center_y), rotation_angle_deg, 1.0)
                rotated = cv2.warpAffine(
                    image_rgb, rot_mat, (img_w, img_h),
                    flags=cv2.INTER_LANCZOS4,
                    borderMode=cv2.BORDER_REPLICATE
                )
            else:
                rotated = image_rgb

            # 2. Clamp crop boundaries
            x1 = max(0, min(img_w - 1, int(crop_x)))
            y1 = max(0, min(img_h - 1, int(crop_y)))
            x2 = max(x1 + 10, min(img_w, int(crop_x + crop_w)))
            y2 = max(y1 + 10, min(img_h, int(crop_y + crop_h)))

            cropped = rotated[y1:y2, x1:x2]

            # 3. High-quality resampling using Lanczos interpolation
            resampled = cv2.resize(
                cropped,
                (target_w, target_h),
                interpolation=cv2.INTER_LANCZOS4
            )
            return resampled

        except Exception as e:
            logger.error(f"Error during crop_and_resize: {e}")
            # Fallback simple slice & resize
            x1 = max(0, int(crop_x))
            y1 = max(0, int(crop_y))
            cropped = image_rgb[y1:y1 + int(crop_h), x1:x1 + int(crop_w)]
            try:
                import cv2
                return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)
            except Exception:
                return cropped
