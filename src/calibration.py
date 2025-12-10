"""Calibration workflow for personalized blink thresholds and gaps."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, stdev
from typing import List

from utils import Thresholds, save_thresholds, load_thresholds


@dataclass
class CalibrationSample:
    duration: float


@dataclass
class CalibrationProfile:
    thresholds: Thresholds
    samples: List[CalibrationSample] = field(default_factory=list)

    def add_sample(self, duration: float) -> None:
        self.samples.append(CalibrationSample(duration))

    def is_ready(self, min_samples: int = 8) -> bool:
        return len(self.samples) >= min_samples

    def compute_thresholds(self) -> Thresholds:
        if not self.samples:
            return self.thresholds
        
        durations = [sample.duration for sample in self.samples]
        
        # Remove outliers (anything > 2 std deviations away)
        if len(durations) >= 5:
            avg = mean(durations)
            std = stdev(durations)
            durations = [d for d in durations if abs(d - avg) <= 2 * std]
        
        if not durations:
            return self.thresholds
            
        avg = mean(durations)
        min_dur = min(durations)
        max_dur = max(durations)
        
        # IMPROVED: Use actual min/max from samples with safety margins
        # Short threshold: 80% of shortest blink (leaves room for even faster blinks)
        short_threshold = max(0.08, min_dur * 0.8)
        
        # Long threshold: 120% of average OR 80% of longest, whichever is higher
        long_threshold = max(avg * 1.2, max_dur * 0.8, short_threshold + 0.2)
        
        # Ensure minimum separation
        if long_threshold - short_threshold < 0.2:
            long_threshold = short_threshold + 0.2
        
        symbol_gap = max(0.4, avg * 1.5)
        letter_gap = symbol_gap * 2.5
        word_gap = letter_gap * 2
        
        self.thresholds = Thresholds(
            short_blink_max=short_threshold,
            long_blink_min=long_threshold,
            symbol_gap=symbol_gap,
            letter_gap=letter_gap,
            word_gap=word_gap,
        )
        return self.thresholds


class CalibrationManager:
    """Handles persistence and runtime calibration sessions."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.profile = CalibrationProfile(thresholds=load_thresholds(storage_path))

    def record_blink(self, duration: float) -> Thresholds:
        # Accept wider range of samples
        if 0.04 <= duration <= 2.5:
            self.profile.add_sample(duration)
            
        if self.profile.is_ready():
            thresholds = self.profile.compute_thresholds()
            save_thresholds(self.storage_path, thresholds)
            return thresholds
        return self.profile.thresholds

    def get_thresholds(self) -> Thresholds:
        return self.profile.thresholds

    def reset(self):
        self.profile.samples.clear()