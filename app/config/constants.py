"""
PhotoPro Central Configuration and Geometric Constants
Contains paper sizes, passport photo standards, and biometric guidelines.
"""
from dataclasses import dataclass
from typing import Dict, Tuple

# Physical Output Resolution
DPI: int = 300
MM_PER_INCH: float = 25.4
PX_PER_MM: float = DPI / MM_PER_INCH  # ~11.81102 px per mm

# Minimum gap between photos on sheet (in millimeters)
MIN_GAP_MM: float = 2.0

# Standard Paper Sizes (Width x Height in mm)
@dataclass(frozen=True)
class PaperFormat:
    key: str
    name: str
    width_mm: float
    height_mm: float

    @property
    def width_px(self) -> int:
        return round(self.width_mm * PX_PER_MM)

    @property
    def height_px(self) -> int:
        return round(self.height_mm * PX_PER_MM)


PAPERS: Dict[str, PaperFormat] = {
    "4R": PaperFormat(key="4R", name="4R (6×4 in)", width_mm=152.4, height_mm=101.6),
    "A4": PaperFormat(key="A4", name="A4 (210×297 mm)", width_mm=210.0, height_mm=297.0),
}

# Standard Photo Sizes (Width x Height in mm)
@dataclass(frozen=True)
class PhotoFormat:
    key: str
    name: str
    width_mm: float
    height_mm: float
    # Biometric standard: Crown-to-chin percentage of height (ISO/IEC 19794-5)
    head_ratio_min: float = 0.68
    head_ratio_max: float = 0.80

    @property
    def width_px(self) -> int:
        return round(self.width_mm * PX_PER_MM)

    @property
    def height_px(self) -> int:
        return round(self.height_mm * PX_PER_MM)

    @property
    def aspect_ratio(self) -> float:
        return self.width_mm / self.height_mm


PHOTO_SIZES: Dict[str, PhotoFormat] = {
    "passport": PhotoFormat(
        key="passport",
        name="Passport Size (35×45 mm)",
        width_mm=35.0,
        height_mm=45.0,
    ),
    "smaller": PhotoFormat(
        key="smaller",
        name="Smaller Size (30×40 mm)",
        width_mm=30.0,
        height_mm=40.0,
    ),
}

# Standard Studio Background Colors (RGB)
PRESET_COLORS: Dict[str, Tuple[int, int, int]] = {
    "white": (255, 255, 255),
    "blue": (31, 111, 178),     # #1F6FB2 standard ID photo blue
    "grey": (229, 231, 235),    # #E5E7EB standard neutral grey
}

# Model paths relative to application root
DEFAULT_MODEL_PATH: str = "u2netp.onnx"
DEFAULT_DB_PATH: str = "photopro.db"
