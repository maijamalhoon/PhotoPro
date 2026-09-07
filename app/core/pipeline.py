"""
PhotoPro Master Image Processing Pipeline
Orchestrates end-to-end processing:
Input -> Face Detection -> Auto-Crop -> Enhancement -> Background Replacement -> 300 DPI Sheet
"""
from __future__ import annotations
import time
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import numpy as np

from app.config.constants import (
    DPI, PAPERS, PHOTO_SIZES, DEFAULT_MODEL_PATH
)
from app.config.settings import AppSettings
from app.ai.face_detector import FaceDetector, FaceLandmarks, BiometricCrop
from app.ai.background_remover import BackgroundRemover
from app.image_processing.enhancer import PhotoEnhancer
from app.image_processing.crop import ImageCropper
from app.image_processing.sheet_generator import SheetGenerator, GridLayout

logger = logging.getLogger(__name__)

@dataclass
class PipelineResult:
    original_rgb: np.ndarray
    landmarks: Optional[FaceLandmarks]
    crop: BiometricCrop
    single_photo_rgb: np.ndarray
    sheet_rgb: Optional[np.ndarray] = None
    grid_layout: Optional[GridLayout] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None

class PhotoProPipeline:
    """Master workflow manager for passport photo generation."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.face_detector = FaceDetector()
        self.bg_remover = BackgroundRemover(model_path=model_path)
        self.enhancer = PhotoEnhancer()
        self.sheet_generator = SheetGenerator()

    @staticmethod
    def load_image_rgb(file_path: str) -> np.ndarray:
        """Loads an image file into an RGB NumPy array."""
        try:
            from PIL import Image, ImageOps
            with Image.open(file_path) as img:
                # Transpose EXIF orientation automatically
                transposed = ImageOps.exif_transpose(img)
                rgb = transposed.convert("RGB")
                return np.array(rgb)
        except Exception as e:
            logger.error(f"Failed to load image from {file_path}: {e}")
            raise

    def process_photo(
        self,
        image_rgb: np.ndarray,
        settings: Optional[AppSettings] = None,
        photo_size_key: str = "passport",
        bg_mode: str = "white",
        custom_color: Tuple[int, int, int] = (31, 111, 178),
        manual_crop: Optional[BiometricCrop] = None,
        manual_brightness: int = 0,
        manual_contrast: int = 0,
        manual_saturation: int = 0,
        paper_key: Optional[str] = "4R",
        copies: int = 8
    ) -> PipelineResult:
        """
        Executes the full automated passport photo pipeline:
        1. Face detection & landmark extraction
        2. Biometric auto-positioning & horizon leveling
        3. High-precision cropping & 300 DPI resampling
        4. Intelligent skin retouching, face brightness lift, and unsharp masking
        5. AI background removal & studio backdrop compositing
        6. Printable 300 DPI sheet layout generation (optional)
        """
        start_time = time.perf_counter()
        cfg = settings or AppSettings()

        h, w = image_rgb.shape[:2]

        # 1. Face Detection & Landmark Extraction
        try:
            import cv2
            bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
            landmarks = self.face_detector.detect(bgr)
        except Exception:
            landmarks = None

        # 2. Biometric Positioning & Crop
        target_format = PHOTO_SIZES.get(photo_size_key, PHOTO_SIZES["passport"])
        if manual_crop is not None:
            crop = manual_crop
        else:
            crop = self.face_detector.calculate_passport_crop(
                w, h, landmarks, target_aspect_ratio=target_format.aspect_ratio
            )

        # 3. Crop and Resample to Target Dimensions at 300 DPI
        cropped_tile = ImageCropper.crop_and_resize(
            image_rgb,
            crop_x=crop.crop_x,
            crop_y=crop.crop_y,
            crop_w=crop.crop_w,
            crop_h=crop.crop_h,
            rotation_angle_deg=crop.rotation_angle_deg,
            photo_size_key=photo_size_key
        )

        # 4. Automated Portrait Enhancement Pipeline
        enhanced_tile = self.enhancer.enhance_full_pipeline(
            cropped_tile,
            auto_skin_retouch=cfg.auto_skin_retouch,
            retouch_strength=cfg.retouch_strength,
            auto_brightness=cfg.face_brightness_lift,
            auto_color_grading=cfg.color_grading,
            auto_sharpen=cfg.unsharp_mask,
            manual_brightness=manual_brightness,
            manual_contrast=manual_contrast,
            manual_saturation=manual_saturation
        )

        # 5. AI Background Removal & Studio Backdrop Replacement
        final_single = self.bg_remover.replace_background(
            enhanced_tile,
            bg_mode=bg_mode,
            custom_color=custom_color
        )

        # 6. Sheet Generation
        sheet_rgb = None
        grid_layout = None
        if paper_key and copies > 0:
            try:
                sheet_rgb, grid_layout = self.sheet_generator.render_sheet(
                    final_single,
                    paper_key=paper_key,
                    photo_size_key=photo_size_key,
                    count=copies,
                    draw_crop_marks=True
                )
            except Exception as e:
                logger.warning(f"Could not generate sheet: {e}")

        duration = (time.perf_counter() - start_time) * 1000.0

        return PipelineResult(
            original_rgb=image_rgb,
            landmarks=landmarks,
            crop=crop,
            single_photo_rgb=final_single,
            sheet_rgb=sheet_rgb,
            grid_layout=grid_layout,
            processing_time_ms=duration
        )
