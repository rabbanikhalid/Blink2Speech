"""Morse code buffering, decoding, and quick command handling - FIXED VERSION."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from enum import Enum

from utils import MORSE_CODE_DICT, QUICK_COMMANDS, Thresholds


class DecoderMode(Enum):
    IDLE = "idle"  # Waiting for first blink
    BUILDING_SYMBOL = "building"  # Actively receiving dots/dashes
    CONFIRMING_LETTER = "confirming"  # Waiting to see if more symbols coming
    CONFIRMING_WORD = "confirming_word"  # Waiting to see if new letter coming


@dataclass
class DecoderState:
    current_letter: str = ""
    output_text: str = ""
    last_symbol_time: Optional[float] = None
    last_letter_time: Optional[float] = None
    mode: DecoderMode = DecoderMode.IDLE
    confirmation_start: Optional[float] = None  # When we started waiting


@dataclass
class MorseDecoderConfig:
    thresholds: Thresholds
    # NEW: Grace periods for confirmation
    symbol_confirmation_time: float = 1.5  # Wait this long after last symbol before finalizing letter
    letter_confirmation_time: float = 3.0  # Wait this long before adding space


class MorseDecoder:
    def __init__(self, config: MorseDecoderConfig):
        self.config = config
        self.state = DecoderState()

    def update_thresholds(self, thresholds: Thresholds) -> None:
        self.config.thresholds = thresholds

    def reset(self) -> None:
        self.state = DecoderState()

    def register_symbol(self, symbol: str, timestamp: float) -> Dict[str, str]:
        """Append a dot or dash and return the updated state snapshot."""
        self.state.current_letter += symbol
        self.state.last_symbol_time = timestamp
        
        # Reset to building mode - user is actively typing
        self.state.mode = DecoderMode.BUILDING_SYMBOL
        self.state.confirmation_start = None
        
        return self._snapshot("symbol")

    def handle_gap(self, timestamp: float) -> Optional[Dict[str, str]]:
        """Conclude letters or words based on timing gaps - BUT WITH STATE AWARENESS."""
        
        # No activity yet
        if self.state.last_symbol_time is None:
            return None
        
        gap = timestamp - self.state.last_symbol_time
        
        # STATE MACHINE LOGIC
        if self.state.mode == DecoderMode.BUILDING_SYMBOL:
            # Just got a symbol, now waiting to see if more coming
            if gap >= self.config.symbol_confirmation_time:
                # User has paused long enough - start confirming this letter
                self.state.mode = DecoderMode.CONFIRMING_LETTER
                self.state.confirmation_start = timestamp
                return None  # Don't finalize yet, just change state
            return None  # Still in grace period
        
        elif self.state.mode == DecoderMode.CONFIRMING_LETTER:
            # We're waiting to finalize the letter
            confirmation_duration = timestamp - (self.state.confirmation_start or timestamp)
            
            if confirmation_duration >= 1.0:  # After 1 more second of no activity
                self._finalize_letter()
                self.state.mode = DecoderMode.CONFIRMING_WORD
                self.state.confirmation_start = timestamp
                return self._snapshot("letter_finalized")
            return None  # Still confirming
        
        elif self.state.mode == DecoderMode.CONFIRMING_WORD:
            # Letter is done, waiting to see if user wants a space
            confirmation_duration = timestamp - (self.state.confirmation_start or timestamp)
            
            if confirmation_duration >= 2.0:  # After 2 more seconds, add space
                if self.state.output_text and not self.state.output_text.endswith(" "):
                    self.state.output_text += " "
                self.state.mode = DecoderMode.IDLE
                self.state.last_symbol_time = None
                return self._snapshot("word_gap")
            return None  # Still confirming
        
        return None

    def _finalize_letter(self) -> None:
        if not self.state.current_letter:
            return
        morse = self.state.current_letter
        if morse in QUICK_COMMANDS:
            phrase = QUICK_COMMANDS[morse]
            self.state.output_text += phrase + " "
        else:
            letter = MORSE_CODE_DICT.get(morse, "?")  # Use "?" for unknown patterns
            if letter:
                self.state.output_text += letter
        self.state.current_letter = ""
        self.state.last_letter_time = None

    def get_translation(self) -> str:
        return self.state.output_text.strip()
    
    def get_current_buffer_preview(self) -> str:
        """Show what the current buffer would translate to."""
        if not self.state.current_letter:
            return ""
        return MORSE_CODE_DICT.get(self.state.current_letter, "?")

    def _snapshot(self, event_type: str) -> Dict[str, str]:
        return {
            "event": event_type,
            "buffer": self.state.current_letter,
            "output": self.state.output_text.strip(),
            "mode": self.state.mode.value,
        }