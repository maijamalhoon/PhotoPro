"""
PhotoPro High-Resolution Exporter
Exports individual photos and sheets to JPG (with 300 DPI EXIF), PNG, and PDF formats.
"""
import os
import logging
from typing import Optional, Tuple
import numpy as np

from app.config.constants import DPI, PAPERS, PHOTO_SIZES

logger = logging.getLogger(__name__)

class ImageExporter:
    """Exports processed images and print sheets to standard file formats."""

    @staticmethod
    def export_jpg(
        image_rgb: np.ndarray,
        filepath: str,
        quality: int = 96
    ) -> bool:
        """Saves image as JPEG with embedded 300 DPI JFIF metadata."""
        try:
            from PIL import Image
            img = Image.fromarray(image_rgb)
            img.save(
                filepath,
                format="JPEG",
                quality=quality,
                dpi=(DPI, DPI),
                subsampling=0  # 4:4:4 chroma for crisp edges
            )
            logger.info(f"Saved 300 DPI JPG to {filepath}")
            return True
        except Exception as e:
            logger.error(f"JPG export failed: {e}")
            return False

    @staticmethod
    def export_png(
        image_rgb: np.ndarray,
        filepath: str
    ) -> bool:
        """Saves lossless PNG with embedded 300 DPI metadata."""
        try:
            from PIL import Image
            img = Image.fromarray(image_rgb)
            img.save(
                filepath,
                format="PNG",
                dpi=(DPI, DPI),
                optimize=True
            )
            logger.info(f"Saved 300 DPI PNG to {filepath}")
            return True
        except Exception as e:
            logger.error(f"PNG export failed: {e}")
            return False

    @staticmethod
    def export_pdf(
        image_rgb: np.ndarray,
        filepath: str,
        paper_key: str = "4R"
    ) -> bool:
        """
        Saves 300 DPI sheet image as an exact-dimension PDF document.
        Calibrates page size in points (72 pt per inch) so PDF viewers
        and print spoolers retain 100% true physical millimeters.
        """
        try:
            from PIL import Image
            paper = PAPERS.get(paper_key, PAPERS["4R"])
            img = Image.fromarray(image_rgb)

            # Convert RGB image directly to PDF with 300 DPI resolution
            img.save(
                filepath,
                format="PDF",
                resolution=float(DPI),
                save_all=True
            )
            logger.info(f"Saved calibrated PDF ({paper.name}) to {filepath}")
            return True
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return False
