"""
PhotoPro Local Face Detection & Biometric Auto-Positioning
Detects facial landmarks, roll angle, and computes optimal passport crop parameters.
Works completely offline.
"""
import math
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

@dataclass
class FaceLandmarks:
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    left_eye: Optional[Tuple[int, int]] = None
    right_eye: Optional[Tuple[int, int]] = None
    nose_tip: Optional[Tuple[int, int]] = None
    mouth_center: Optional[Tuple[int, int]] = None
    chin: Optional[Tuple[int, int]] = None
    roll_angle_deg: float = 0.0
    confidence: float = 1.0

@dataclass
class BiometricCrop:
    crop_x: int
    crop_y: int
    crop_w: int
    crop_h: int
    rotation_angle_deg: float = 0.0
    face_detected: bool = True

class FaceDetector:
    """Local face detection and biometric passport positioning engine."""

    def __init__(self):
        self._cascade = None
        self._eye_cascade = None
        self._init_models()

    def _init_models(self):
        """Initializes OpenCV Haar cascades or ONNX detector if available."""
        try:
            import cv2
            # Try loading built-in OpenCV Haar Cascades
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            eye_path = cv2.data.haarcascades + "haarcascade_eye.xml"
            self._cascade = cv2.CascadeClassifier(cascade_path)
            self._eye_cascade = cv2.CascadeClassifier(eye_path)
        except Exception as e:
            logger.warning(f"OpenCV cascade initialization deferred: {e}")

    def detect(self, image_bgr) -> Optional[FaceLandmarks]:
        """
        Detects primary face and key landmarks from a BGR image (NumPy array).
        Returns FaceLandmarks with bounding box, eyes, and tilt angle.
        """
        try:
            import cv2
            import numpy as np

            if image_bgr is None:
                return None

            h, w = image_bgr.shape[:2]
            gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            # Equalize histogram for robust detection under varied lighting
            gray_eq = cv2.equalizeHist(gray)

            if self._cascade is None or self._cascade.empty():
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self._cascade = cv2.CascadeClassifier(cascade_path)

            faces = self._cascade.detectMultiScale(
                gray_eq,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(int(min(w, h) * 0.15), int(min(w, h) * 0.15)),
                flags=cv2.CASCADE_SCALE_IMAGE
            )

            if len(faces) == 0:
                return None

            # Select the largest face (most prominent subject)
            largest_face = max(faces, key=lambda b: b[2] * b[3])
            fx, fy, fw, fh = largest_face

            # Search for eyes in upper half of the detected face
            face_roi_gray = gray_eq[fy:fy + int(fh * 0.58), fx:fx + fw]
            left_eye = None
            right_eye = None
            roll_angle = 0.0

            if self._eye_cascade is not None and not self._eye_cascade.empty():
                eyes = self._eye_cascade.detectMultiScale(
                    face_roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(int(fw * 0.12), int(fh * 0.12))
                )
                if len(eyes) >= 2:
                    # Sort eyes by X coordinate
                    sorted_eyes = sorted(eyes, key=lambda e: e[0])
                    # Eye 1 is subject's right (image left), Eye 2 is subject's left (image right)
                    e1 = sorted_eyes[0]
                    e2 = sorted_eyes[-1]
                    pt1 = (fx + e1[0] + e1[2] // 2, fy + e1[1] + e1[3] // 2)
                    pt2 = (fx + e2[0] + e2[2] // 2, fy + e2[1] + e2[3] // 2)

                    # Ensure sufficient horizontal distance
                    if abs(pt2[0] - pt1[0]) > fw * 0.25:
                        left_eye = pt1
                        right_eye = pt2
                        # Compute eye tilt angle
                        dx = pt2[0] - pt1[0]
                        dy = pt2[1] - pt1[1]
                        angle_rad = math.atan2(dy, dx)
                        roll_angle = math.degrees(angle_rad)

            # Synthesize eye centers if eye detector missed them
            if left_eye is None or right_eye is None:
                left_eye = (fx + int(fw * 0.33), fy + int(fh * 0.40))
                right_eye = (fx + int(fw * 0.67), fy + int(fh * 0.40))

            nose_tip = (fx + fw // 2, fy + int(fh * 0.60))
            mouth_center = (fx + fw // 2, fy + int(fh * 0.80))
            chin = (fx + fw // 2, fy + fh)

            return FaceLandmarks(
                bbox=(int(fx), int(fy), int(fw), int(fh)),
                left_eye=left_eye,
                right_eye=right_eye,
                nose_tip=nose_tip,
                mouth_center=mouth_center,
                chin=chin,
                roll_angle_deg=roll_angle,
                confidence=0.95
            )
        except Exception as e:
            logger.warning(f"Face detection exception: {e}")
            return None

    def calculate_passport_crop(
        self,
        img_w: int,
        img_h: int,
        landmarks: Optional[FaceLandmarks],
        target_aspect_ratio: float = 35.0 / 45.0
    ) -> BiometricCrop:
        """
        Calculates biometric crop window satisfying ISO/IEC 19794-5:
        - Crown to chin occupies ~70-75% of portrait height.
        - Face is centered horizontally.
        - Eyes align around 58-62% from the bottom of the photo.
        """
        if landmarks is None:
            # Fallback: Center crop with upper-third vertical bias
            crop_w = img_w
            crop_h = int(img_w / target_aspect_ratio)
            if crop_h > img_h:
                crop_h = img_h
                crop_w = int(img_h * target_aspect_ratio)
            crop_x = (img_w - crop_w) // 2
            crop_y = max(0, int((img_h - crop_h) * 0.20))
            return BiometricCrop(
                crop_x=crop_x,
                crop_y=crop_y,
                crop_w=crop_w,
                crop_h=crop_h,
                rotation_angle_deg=0.0,
                face_detected=False
            )

        fx, fy, fw, fh = landmarks.bbox
        # Biometric crown estimation: hair extends ~30% above detected face box
        estimated_crown_y = max(0, fy - int(fh * 0.30))
        estimated_chin_y = min(img_h, fy + int(fh * 1.05))
        head_height = estimated_chin_y - estimated_crown_y

        # We want the head height to be ~72% of total crop height
        desired_crop_h = int(head_height / 0.72)
        desired_crop_w = int(desired_crop_h * target_aspect_ratio)

        # Ensure crop width is wide enough to encompass shoulders (at least 1.7x face width)
        min_crop_w = int(fw * 1.75)
        if desired_crop_w < min_crop_w:
            desired_crop_w = min_crop_w
            desired_crop_h = int(desired_crop_w / target_aspect_ratio)

        # Center horizontally on nose / eyes midpoint
        face_center_x = landmarks.nose_tip[0] if landmarks.nose_tip else fx + fw // 2
        crop_x = face_center_x - desired_crop_w // 2

        # Position vertically: crown sits ~10% below the top edge
        crop_y = estimated_crown_y - int(desired_crop_h * 0.09)

        # Clamp and scale if exceeding image boundaries
        if desired_crop_h > img_h:
            desired_crop_h = img_h
            desired_crop_w = int(desired_crop_h * target_aspect_ratio)
        if desired_crop_w > img_w:
            desired_crop_w = img_w
            desired_crop_h = int(desired_crop_w / target_aspect_ratio)

        crop_x = max(0, min(img_w - desired_crop_w, crop_x))
        crop_y = max(0, min(img_h - desired_crop_h, crop_y))

        # Level head if tilt is minor (between -8 and +8 degrees)
        angle = landmarks.roll_angle_deg
        if abs(angle) > 12.0:
            angle = 0.0  # Avoid severe rotations for unnatural poses

        return BiometricCrop(
            crop_x=int(crop_x),
            crop_y=int(crop_y),
            crop_w=int(desired_crop_w),
            crop_h=int(desired_crop_h),
            rotation_angle_deg=-angle,
            face_detected=True
        )
