"""Application entry-point wiring together detectors, decoder, GUI, and TTS."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2

from blink_detector import BlinkDetector, BlinkDetectorConfig
from calibration import CalibrationManager
from gui import AppGUI, GUIConfig
from morse_decoder import MorseDecoder, MorseDecoderConfig
from tts_engine import TTSEngine, TTSEngineConfig
from utils import QUICK_COMMANDS, MORSE_CODE_DICT, Thresholds, current_timestamp


class MainApp:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.thresholds_path = self.config_dir / "thresholds.json"

        self.calibration_manager = CalibrationManager(self.thresholds_path)
        thresholds = self.calibration_manager.get_thresholds()

        self.blink_detector = BlinkDetector(BlinkDetectorConfig())
        self.decoder = MorseDecoder(MorseDecoderConfig(thresholds=thresholds))
        self.tts = TTSEngine(TTSEngineConfig())
        self.gui = AppGUI(
            GUIConfig(),
            on_speak=self.handle_speak,
            on_quick_command=self.handle_quick_command,
            morse_dict=MORSE_CODE_DICT,
            quick_commands=QUICK_COMMANDS,
        )

        self.gui.on_clear = self.handle_clear
        self.calibrating = not self.calibration_manager.profile.is_ready()
        
        # Debug tracking
        self.last_blink_time = None
        self.blink_count = 0

    def start(self):
        self.gui.root.after(10, self._update_loop)
        self.gui.mainloop()

    def _update_loop(self):
        ret, frame = self.gui.camera.read()
        dotdash = ""
        blink_state = "Searching"

        translation = self.decoder.get_translation() or ""
        morse_buffer = self.decoder.state.current_letter or ""
        mode = self.decoder.state.mode.value
        preview = self.decoder.get_current_buffer_preview() or ""

        ear_value: Optional[float] = None

        if ret:
            timestamp = current_timestamp()
            metrics, blink_event = self.blink_detector.process(frame, timestamp)
            blink_state = f"EAR={metrics['ear']:.3f}"
            ear_value = metrics.get("ear", 0.0)

            if blink_event and blink_event.is_blink:
                self.blink_count += 1
                self.last_blink_time = timestamp
                
                if self.calibrating:
                    thresholds = self.calibration_manager.record_blink(blink_event.duration)
                    self.decoder.update_thresholds(thresholds)
                    
                    if self.calibration_manager.profile.is_ready():
                        self.calibrating = False
                        # Show final thresholds
                        t = thresholds
                        msg = f"✅ Calibrated! Short: <{t.short_blink_max:.2f}s, Long: >{t.long_blink_min:.2f}s"
                        self.gui.status_bar_var.set(msg)
                    else:
                        needed = 8 - len(self.calibration_manager.profile.samples)
                        blink_state = f"Calibrating... {needed} more blinks needed"
                else:
                    thresholds = self.calibration_manager.get_thresholds()
                    
                    # Classify with clear boundaries
                    if blink_event.duration < thresholds.short_blink_max:
                        symbol = "."
                        dotdash = f"DOT ({blink_event.duration:.2f}s)"
                    elif blink_event.duration >= thresholds.long_blink_min:
                        symbol = "-"
                        dotdash = f"DASH ({blink_event.duration:.2f}s)"
                    else:
                        # In the dead zone - ignore
                        dotdash = f"IGNORED ({blink_event.duration:.2f}s - between thresholds)"
                        symbol = None
                    
                    if symbol:
                        snapshot = self.decoder.register_symbol(symbol, timestamp)
                        morse_buffer = snapshot["buffer"]
                        translation = snapshot["output"]
                        mode = snapshot.get("mode", "idle")
                        preview = self.decoder.get_current_buffer_preview()

            # Handle gaps ONLY when not calibrating
            if not self.calibrating:
                gap_snapshot = self.decoder.handle_gap(timestamp)
                if gap_snapshot:
                    morse_buffer = gap_snapshot["buffer"]
                    translation = gap_snapshot["output"]
                    mode = gap_snapshot.get("mode", "idle")
                    preview = self.decoder.get_current_buffer_preview()

            self.gui.display_frame(frame)
        else:
            blink_state = "Camera frame unavailable"

        self.gui.set_status(
            blink_state=blink_state,
            morse_buffer=morse_buffer,
            translation=translation,
            dotdash=dotdash,
            ear_value=ear_value,
            mode=mode,
            preview=preview,
        )

        self.gui.root.after(10, self._update_loop)

    def handle_speak(self):
        text = self.decoder.get_translation()
        if text:
            self.tts.speak(text)
        else:
            self.gui.status_bar_var.set("⚠️ Nothing to speak!")

    def handle_quick_command(self, phrase: str):
        self.tts.speak(phrase)
        self.gui.status_bar_var.set(f"🚨 Speaking: {phrase}")

    def handle_clear(self):
        self.decoder.reset()
        self.gui.clear_translation()
        self.gui.morse_var.set("...")
        self.gui.preview_var.set("—")
        self.gui.status_bar_var.set("🗑️ Cleared text.")
        
    def teardown(self):
        self.gui.teardown()
        self.blink_detector.release()


if __name__ == "__main__":
    app = MainApp()
    try:
        app.start()
    finally:
        app.teardown()