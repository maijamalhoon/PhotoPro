"""
PhotoPro Application Settings Manager
Loads and saves persistent settings from local SQLite storage.
"""
import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class AppSettings:
    default_paper: str = "4R"
    default_photo_size: str = "passport"
    default_background: str = "white"
    default_custom_color: str = "#1F6FB2"
    default_copies: int = 8
    auto_face_position: bool = True
    auto_enhance: bool = True
    auto_skin_retouch: bool = True
    retouch_strength: int = 50  # 0 to 100
    face_brightness_lift: bool = True
    color_grading: bool = True
    unsharp_mask: bool = True
    export_quality: int = 96
    hardware_acceleration: str = "auto"  # "auto", "cpu", "directml", "cuda"
    default_printer: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)
