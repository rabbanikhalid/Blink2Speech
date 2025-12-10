"""Shared utilities, constants, and helper functions for the AI Eye-Blink Morse Code Translator."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple
import json
import time

# Commonly referenced MediaPipe Face Mesh eye landmark indices (right/left)
RIGHT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
LEFT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]


MORSE_CODE_DICT: Dict[str, str] = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
    # Numbers
    "-----": "0",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    # Punctuation
    ".-.-.-": ".",
    "--..--": ",",
    "..--..": "?",
    ".----.": "'",
    "-.-.--": "!",
    "-..-.": "/",
    "-.--.": "(",
    "-.--.-": ")",
    ".-..-.": "\"",
    "---...": ":",
    "-.-.-.": ";",
    "-...-": "=",
    ".-.-.": "+",
    "-....-": "-",
    "..--.-": "_",
    ".--.-.": "@",
}

# EMERGENCY QUICK COMMANDS - These override normal morse decoding
QUICK_COMMANDS: Dict[str, str] = {
    "...---...": "HELP! EMERGENCY!",  # SOS in morse
    "..--.": "I need water",
    "--..--": "Call the nurse",
    ".-.-": "I am in pain",
    "..--": "Thank you",
    "---...---": "I need medication",
}


@dataclass
class Thresholds:
    """Container for blink classification thresholds and gap timings."""

    # VERY GENEROUS DEFAULTS - almost anything quick is a dot
    short_blink_max: float = 0.30  # Anything under 0.30s = DOT
    long_blink_min: float = 0.50   # Anything over 0.50s = DASH
    # 0.20s buffer zone (0.30-0.50)
    
    symbol_gap: float = 0.5
    letter_gap: float = 1.5
    word_gap: float = 3.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "short_blink_max": self.short_blink_max,
            "long_blink_min": self.long_blink_min,
            "symbol_gap": self.symbol_gap,
            "letter_gap": self.letter_gap,
            "word_gap": self.word_gap,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, float]) -> "Thresholds":
        return cls(
            short_blink_max=payload.get("short_blink_max", 0.30),
            long_blink_min=payload.get("long_blink_min", 0.50),
            symbol_gap=payload.get("symbol_gap", 0.5),
            letter_gap=payload.get("letter_gap", 1.5),
            word_gap=payload.get("word_gap", 3.0),
        )


def load_thresholds(path: Path) -> Thresholds:
    if not path.exists():
        return Thresholds()
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return Thresholds.from_dict(data)


def save_thresholds(path: Path, thresholds: Thresholds) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(thresholds.to_dict(), handle, indent=2)


def current_timestamp() -> float:
    """Return a monotonic timestamp in seconds."""
    return time.perf_counter()