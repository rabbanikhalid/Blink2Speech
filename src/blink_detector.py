"""Blink detection module using MediaPipe Face Mesh and Eye Aspect Ratio (EAR)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict

import cv2
import mediapipe as mp
import numpy as np

from utils import LEFT_EYE_LANDMARKS, RIGHT_EYE_LANDMARKS


@dataclass
class BlinkDetectorConfig:
    eye_ar_threshold: float = 0.18  # Higher = more sensitive
    eye_ar_smooth_factor: float = 0.7  # Lower = faster response (0.5 = 50% new, 50% old)
    min_blink_duration: float = 0.03  # Very short minimum
    max_blink_duration: float = 3.0
    debounce_time: float = 0.08  # Short debounce


@dataclass
class BlinkEvent:
    is_blink: bool
    duration: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    message: str = ""


class BlinkDetector:
    """Processes video frames, tracks eye aspect ratio, and emits blink events."""

    def __init__(self, config: BlinkDetectorConfig | None = None):
        self.config = config or BlinkDetectorConfig()
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.prev_ear: Optional[float] = None
        self.eye_closed = False
        self.blink_start: Optional[float] = None
        self.last_blink_end: Optional[float] = None

    @staticmethod
    def _eye_aspect_ratio(landmarks: np.ndarray) -> float:
        """Compute the eye aspect ratio from six landmark coordinates."""
        p2_minus_p6 = np.linalg.norm(landmarks[1] - landmarks[5])
        p3_minus_p5 = np.linalg.norm(landmarks[2] - landmarks[4])
        p1_minus_p4 = np.linalg.norm(landmarks[0] - landmarks[3])
        ear = (p2_minus_p6 + p3_minus_p5) / (2.0 * p1_minus_p4 + 1e-6)
        return ear

    def _extract_eye_landmarks(self, face_landmarks, image_shape) -> Tuple[np.ndarray, np.ndarray]:
        h, w = image_shape[:2]
        coords = np.array(
            [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]
        )
        right_eye = coords[RIGHT_EYE_LANDMARKS]
        left_eye = coords[LEFT_EYE_LANDMARKS]
        return right_eye, left_eye

    def process(self, frame, timestamp: float) -> Tuple[Dict[str, float], Optional[BlinkEvent]]:
        """Process a BGR frame and return EAR metrics plus an optional blink event."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        metrics = {"ear": 0.0}
        blink_event: Optional[BlinkEvent] = None

        if results.multi_face_landmarks:
            right_eye, left_eye = self._extract_eye_landmarks(
                results.multi_face_landmarks[0], frame.shape
            )
            ear_right = self._eye_aspect_ratio(right_eye.astype(np.float32))
            ear_left = self._eye_aspect_ratio(left_eye.astype(np.float32))
            raw_ear = (ear_left + ear_right) / 2.0
            
            # Simple exponential smoothing - very light
            if self.prev_ear is None:
                smoothed = raw_ear
            else:
                alpha = self.config.eye_ar_smooth_factor
                smoothed = alpha * raw_ear + (1 - alpha) * self.prev_ear
            
            self.prev_ear = smoothed
            metrics["ear"] = smoothed

            # Check debounce
            if self.last_blink_end is not None:
                time_since_last = timestamp - self.last_blink_end
                if time_since_last < self.config.debounce_time:
                    return metrics, None

            # STATE 1: Eye opens -> closes (blink starts)
            if not self.eye_closed and smoothed < self.config.eye_ar_threshold:
                self.eye_closed = True
                self.blink_start = timestamp
                
            # STATE 2: Eye closed -> opens (blink ends)
            elif self.eye_closed and smoothed >= self.config.eye_ar_threshold:
                self.eye_closed = False
                if self.blink_start is not None:
                    duration = timestamp - self.blink_start
                    
                    # Validate duration
                    if self.config.min_blink_duration <= duration <= self.config.max_blink_duration:
                        blink_event = BlinkEvent(
                            is_blink=True,
                            duration=duration,
                            start_time=self.blink_start,
                            end_time=timestamp,
                            message="Blink detected",
                        )
                        self.last_blink_end = timestamp
                        
                self.blink_start = None
        else:
            metrics["ear"] = self.prev_ear or 0.0

        return metrics, blink_event

    def release(self):
        self.face_mesh.close()