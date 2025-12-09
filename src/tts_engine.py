"""Text-to-speech abstraction with pyttsx3 fallback to gTTS."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pyttsx3

try:
    from gtts import gTTS
    from playsound import playsound
except ImportError:  # pragma: no cover
    gTTS = None
    playsound = None


@dataclass
class TTSEngineConfig:
    voice: Optional[str] = None
    rate: int = 180
    volume: float = 1.0
    cache_dir: Path = Path("cache/audio")


class TTSEngine:
    def __init__(self, config: TTSEngineConfig | None = None):
        self.config = config or TTSEngineConfig()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", self.config.rate)
        self.engine.setProperty("volume", self.config.volume)
        if self.config.voice:
            self.engine.setProperty("voice", self.config.voice)
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)

    def speak(self, text: str) -> None:
        if not text:
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except RuntimeError:
            self._speak_with_gtts(text)

    def _speak_with_gtts(self, text: str) -> None:
        if gTTS is None or playsound is None:
            raise RuntimeError("Text-to-speech fallback unavailable; install gTTS and playsound.")
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = self.config.cache_dir / "tts.mp3"
        tts = gTTS(text=text, lang="en")
        tts.save(tmp_file.as_posix())
        playsound(tmp_file.as_posix())


