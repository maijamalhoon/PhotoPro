"""
PhotoPro Sheet Layout and Generation Engine
Calculates optimal grid placement, margins, cutting guides, and corner crop marks
for 4R and A4 paper sizes at exact 300 DPI physical resolution.
"""
from __future__ import annotations
import math
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
try:
    import numpy as np
except ImportError:
    np = None

from app.config.constants import (
    DPI, PX_PER_MM, MIN_GAP_MM,
    PAPERS, PHOTO_SIZES, PaperFormat, PhotoFormat
)

logger = logging.getLogger(__name__)

@dataclass
class GridLayout:
    cols: int
    rows: int
    total_capacity: int
    count_to_place: int
    margin_x_px: int
    margin_y_px: int
    gap_x_px: int
    gap_y_px: int
    photo_w_px: int
    photo_h_px: int
    sheet_w_px: int
    sheet_h_px: int

class SheetGenerator:
    """Calculates photo sheet geometry and renders 300 DPI print-ready sheets."""

    @staticmethod
    def calculate_max_capacity(paper_key: str = "4R", photo_size_key: str = "passport") -> int:
        """Calculates maximum number of photos that can fit on chosen paper."""
        paper = PAPERS.get(paper_key, PAPERS["4R"])
        photo = PHOTO_SIZES.get(photo_size_key, PHOTO_SIZES["passport"])

        max_cols = math.floor((paper.width_mm - MIN_GAP_MM) / (photo.width_mm + MIN_GAP_MM))
        max_rows = math.floor((paper.height_mm - MIN_GAP_MM) / (photo.height_mm + MIN_GAP_MM))
        return max(1, max_cols * max_rows)

    @staticmethod
    def compute_grid_layout(
        paper_key: str,
        photo_size_key: str,
        count: int
    ) -> Optional[GridLayout]:
        """
        Determines the optimal rows, columns, and centered spacing for placing
        `count` photos on the selected paper format.
        """
        paper = PAPERS.get(paper_key, PAPERS["4R"])
        photo = PHOTO_SIZES.get(photo_size_key, PHOTO_SIZES["passport"])

        sheet_w = paper.width_px
        sheet_h = paper.height_px
        photo_w = photo.width_px
        photo_h = photo.height_px

        min_gap_px = int(MIN_GAP_MM * PX_PER_MM)

        max_cols = math.floor((sheet_w - min_gap_px) / (photo_w + min_gap_px))
        max_rows = math.floor((sheet_h - min_gap_px) / (photo_h + min_gap_px))

        if max_cols < 1 or max_rows < 1:
            return None

        # Clamp count to absolute max capacity
        count = min(count, max_cols * max_rows)
        target_aspect = sheet_w / float(sheet_h)
        best_layout = None
        min_waste = float("inf")
        min_aspect_diff = float("inf")

        for cols in range(1, max_cols + 1):
            rows = math.ceil(count / cols)
            if rows > max_rows:
                continue

            waste = cols * rows - count
            grid_aspect = (cols * photo_w) / float(rows * photo_h)
            aspect_diff = abs(math.log(grid_aspect / target_aspect))

            if (waste < min_waste) or (waste == min_waste and aspect_diff < min_aspect_diff):
                min_waste = waste
                min_aspect_diff = aspect_diff
                best_layout = (cols, rows)

        if not best_layout:
            return None

        cols, rows = best_layout
        total_photos_w = cols * photo_w
        total_photos_h = rows * photo_h

        # Distribute remaining space evenly across margins and gaps
        gap_x = max(min_gap_px, (sheet_w - total_photos_w) // (cols + 1))
        gap_y = max(min_gap_px, (sheet_h - total_photos_h) // (rows + 1))

        # Center the grid block on the sheet
        used_w = cols * photo_w + (cols - 1) * gap_x
        used_h = rows * photo_h + (rows - 1) * gap_y
        margin_x = max(0, (sheet_w - used_w) // 2)
        margin_y = max(0, (sheet_h - used_h) // 2)

        return GridLayout(
            cols=cols,
            rows=rows,
            total_capacity=cols * rows,
            count_to_place=count,
            margin_x_px=margin_x,
            margin_y_px=margin_y,
            gap_x_px=gap_x,
            gap_y_px=gap_y,
            photo_w_px=photo_w,
            photo_h_px=photo_h,
            sheet_w_px=sheet_w,
            sheet_h_px=sheet_h,
        )

    @classmethod
    def render_sheet(
        cls,
        photo_tile_rgb: np.ndarray,
        paper_key: str = "4R",
        photo_size_key: str = "passport",
        count: int = 8,
        draw_crop_marks: bool = True
    ) -> Tuple[np.ndarray, GridLayout]:
        """
        Renders full 300 DPI sheet image with crisp white photo paper background,
        individual photo tiles, subtle 1px cutting lines, and precision corner tick marks.
        """
        layout = cls.compute_grid_layout(paper_key, photo_size_key, count)
        if not layout:
            raise ValueError(f"Cannot fit {count} photos on paper {paper_key}")

        try:
            import cv2

            # Ensure photo tile matches exact target dimensions
            th, tw = photo_tile_rgb.shape[:2]
            if tw != layout.photo_w_px or th != layout.photo_h_px:
                photo_tile = cv2.resize(
                    photo_tile_rgb,
                    (layout.photo_w_px, layout.photo_h_px),
                    interpolation=cv2.INTER_LANCZOS4
                )
            else:
                photo_tile = photo_tile_rgb

            # Create solid white 300 DPI sheet canvas
            sheet = np.full((layout.sheet_h_px, layout.sheet_w_px, 3), 255, dtype=np.uint8)

            placed = 0
            tick_len = int(3.0 * PX_PER_MM)  # 3mm corner crop ticks
            border_color = (212, 212, 216)   # subtle light gray cutting line
            tick_color = (156, 163, 175)     # distinct gray trimmer tick

            for r in range(layout.rows):
                for c in range(layout.cols):
                    if placed >= layout.count_to_place:
                        break

                    x = layout.margin_x_px + c * (layout.photo_w_px + layout.gap_x_px)
                    y = layout.margin_y_px + r * (layout.photo_h_px + layout.gap_y_px)

                    # Paste photo tile
                    sheet[y:y + layout.photo_h_px, x:x + layout.photo_w_px] = photo_tile

                    # 1. Subtle 1px rectangular cutting guide
                    cv2.rectangle(
                        sheet,
                        (x, y),
                        (x + layout.photo_w_px - 1, y + layout.photo_h_px - 1),
                        border_color,
                        thickness=1
                    )

                    # 2. Precision corner tick marks for rotary guillotine cutter
                    if draw_crop_marks:
                        # Top-left corner
                        cv2.line(sheet, (x - tick_len, y), (x, y), tick_color, 1)
                        cv2.line(sheet, (x, y - tick_len), (x, y), tick_color, 1)
                        # Top-right corner
                        cv2.line(sheet, (x + layout.photo_w_px, y), (x + layout.photo_w_px + tick_len, y), tick_color, 1)
                        cv2.line(sheet, (x + layout.photo_w_px, y - tick_len), (x + layout.photo_w_px, y), tick_color, 1)
                        # Bottom-left corner
                        cv2.line(sheet, (x - tick_len, y + layout.photo_h_px), (x, y + layout.photo_h_px), tick_color, 1)
                        cv2.line(sheet, (x, y + layout.photo_h_px), (x, y + layout.photo_h_px + tick_len), tick_color, 1)
                        # Bottom-right corner
                        cv2.line(sheet, (x + layout.photo_w_px, y + layout.photo_h_px), (x + layout.photo_w_px + tick_len, y + layout.photo_h_px), tick_color, 1)
                        cv2.line(sheet, (x + layout.photo_w_px, y + layout.photo_h_px), (x + layout.photo_w_px, y + layout.photo_h_px + tick_len), tick_color, 1)

                    placed += 1

            return sheet, layout

        except Exception as e:
            logger.error(f"Sheet rendering error: {e}")
            raise
