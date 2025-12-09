"""Tkinter GUI for the AI Eye-Blink Morse Code Translator - WITH REFERENCE CHART."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict

import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, scrolledtext


@dataclass
class GUIConfig:
    window_title: str = "AI Eye-Blink Morse Code Translator"
    width: int = 1200
    height: int = 700
    camera_index: int = 0


class AppGUI:
    def __init__(
        self,
        config: GUIConfig,
        on_speak: Callable[[], None],
        on_quick_command: Callable[[str], None],
        morse_dict: Dict[str, str],
        quick_commands: Dict[str, str],
    ):
        self.on_clear = None
        self.config = config
        self.on_speak = on_speak
        self.on_quick_command = on_quick_command
        self.morse_dict = morse_dict
        self.quick_commands = quick_commands
        
        self.root = tk.Tk()
        self.root.title(self.config.window_title)
        self.root.geometry(f"{self.config.width}x{self.config.height}")
        self.root.configure(padx=10, pady=10)
        
        # Grid layout: [Video | Controls | Reference Chart]
        self.root.columnconfigure(0, weight=2)  # Video
        self.root.columnconfigure(1, weight=2)  # Controls
        self.root.columnconfigure(2, weight=1)  # Reference
        self.root.rowconfigure(0, weight=1)

        style = ttk.Style(self.root)
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Section.TLabelframe", padding=10)
        style.configure("Emergency.TButton", font=("Segoe UI", 9, "bold"))

        self.status_var = tk.StringVar()
        self.blink_var = tk.StringVar(value="Initializing camera...")
        self.morse_var = tk.StringVar()
        self.translation_var = tk.StringVar()
        self.status_bar_var = tk.StringVar(value="Ready")
        self.ear_var = tk.DoubleVar(value=0.0)
        self.mode_var = tk.StringVar(value="IDLE")
        self.preview_var = tk.StringVar(value="")

        # ========== LEFT COLUMN: VIDEO ==========
        video_frame = ttk.LabelFrame(self.root, text="Live Camera", style="Section.TLabelframe")
        video_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        video_frame.rowconfigure(0, weight=1)
        video_frame.columnconfigure(0, weight=1)

        self.video_label = ttk.Label(video_frame)
        self.video_label.grid(row=0, column=0, sticky="nsew")

        # ========== MIDDLE COLUMN: CONTROLS ==========
        control_panel = ttk.Frame(self.root)
        control_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        control_panel.columnconfigure(0, weight=1)

        # Blink monitor
        blink_frame = ttk.LabelFrame(control_panel, text="Blink Monitor", style="Section.TLabelframe")
        blink_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ttk.Label(blink_frame, text="State:", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(blink_frame, textvariable=self.blink_var).grid(row=0, column=1, sticky="w")
        
        ttk.Label(blink_frame, text="Decoder Mode:", style="Header.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 0))
        mode_label = ttk.Label(blink_frame, textvariable=self.mode_var, font=("Consolas", 10, "bold"), foreground="green")
        mode_label.grid(row=1, column=1, sticky="w")
        
        ttk.Label(blink_frame, text="Last Blink:", style="Header.TLabel").grid(row=2, column=0, sticky="w", pady=(5, 0))
        ttk.Label(blink_frame, textvariable=self.status_var).grid(row=2, column=1, sticky="w")
        
        ttk.Label(blink_frame, text="EAR Level:", style="Header.TLabel").grid(row=3, column=0, sticky="w", pady=(5, 0))
        ear_bar = ttk.Progressbar(blink_frame, variable=self.ear_var, maximum=1.0)
        ear_bar.grid(row=3, column=1, sticky="ew", padx=(5, 0))
        
        blink_frame.columnconfigure(1, weight=1)

        # Morse buffer with preview
        morse_frame = ttk.LabelFrame(control_panel, text="Morse Buffer", style="Section.TLabelframe")
        morse_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        morse_frame.columnconfigure(0, weight=1)
        
        buffer_container = ttk.Frame(morse_frame)
        buffer_container.grid(row=0, column=0, sticky="ew")
        buffer_container.columnconfigure(0, weight=1)
        
        ttk.Label(buffer_container, text="Symbols:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        ttk.Label(buffer_container, textvariable=self.morse_var, font=("Consolas", 16, "bold")).grid(row=1, column=0, sticky="w")
        
        ttk.Label(buffer_container, text="Preview:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=(5, 0))
        preview_label = ttk.Label(buffer_container, textvariable=self.preview_var, font=("Consolas", 20, "bold"), foreground="blue")
        preview_label.grid(row=3, column=0, sticky="w")

        # Translation display
        translation_frame = ttk.LabelFrame(control_panel, text="English Translation", style="Section.TLabelframe")
        translation_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        translation_frame.rowconfigure(0, weight=1)
        translation_frame.columnconfigure(0, weight=1)
        self.translation_box = scrolledtext.ScrolledText(
            translation_frame, height=4, wrap="word", font=("Segoe UI", 11), state="disabled"
        )
        self.translation_box.grid(row=0, column=0, sticky="nsew")

        # Action buttons
        controls = ttk.Frame(control_panel)
        controls.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        controls.columnconfigure((0, 1), weight=1)
        speak_btn = ttk.Button(controls, text="🔊 Speak", command=self.on_speak)
        speak_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        copy_btn = ttk.Button(controls, text="📋 Copy Text", command=self.copy_translation)
        copy_btn.grid(row=0, column=1, sticky="ew")
        clear_btn = ttk.Button(controls, text="🗑 Clear Text", command=lambda: self.on_clear())
        clear_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5,0))


        # Emergency quick commands
        emergency_frame = ttk.LabelFrame(control_panel, text="🚨 Emergency Quick Commands", style="Section.TLabelframe")
        emergency_frame.grid(row=4, column=0, sticky="ew")
        emergency_frame.columnconfigure(0, weight=1)
        
        self._build_emergency_buttons(emergency_frame)

        # ========== RIGHT COLUMN: REFERENCE CHART ==========
        reference_panel = ttk.Frame(self.root)
        reference_panel.grid(row=0, column=2, sticky="nsew")
        reference_panel.rowconfigure(0, weight=1)
        reference_panel.columnconfigure(0, weight=1)

        # Morse code reference
        ref_frame = ttk.LabelFrame(reference_panel, text="📖 Morse Code Reference", style="Section.TLabelframe")
        ref_frame.grid(row=0, column=0, sticky="nsew")
        ref_frame.rowconfigure(0, weight=1)
        ref_frame.columnconfigure(0, weight=1)

        ref_canvas = tk.Canvas(ref_frame, bg="white")
        ref_scrollbar = ttk.Scrollbar(ref_frame, orient="vertical", command=ref_canvas.yview)
        ref_scrollable = ttk.Frame(ref_canvas)

        ref_scrollable.bind(
            "<Configure>",
            lambda e: ref_canvas.configure(scrollregion=ref_canvas.bbox("all"))
        )

        ref_canvas.create_window((0, 0), window=ref_scrollable, anchor="nw")
        ref_canvas.configure(yscrollcommand=ref_scrollbar.set)

        ref_canvas.grid(row=0, column=0, sticky="nsew")
        ref_scrollbar.grid(row=0, column=1, sticky="ns")

        self._build_morse_reference(ref_scrollable)

        # ========== BOTTOM: INSTRUCTIONS & STATUS ==========
        instruction_frame = ttk.LabelFrame(self.root, text="💡 Quick Guide", padding=10)
        instruction_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        instruction_text = (
            "1. Calibrate: Blink naturally 5 times  |  "
            "2. Short blink = dot (·), Long blink = dash (−)  |  "
            "3. Grace period: 1.5s to add more symbols  |  "
            "4. Emergency: Use quick command buttons for instant phrases"
        )
        ttk.Label(instruction_frame, text=instruction_text, wraplength=self.config.width - 40).grid(
            row=0, column=0, sticky="w"
        )

        self.status_bar = ttk.Label(self.root, textvariable=self.status_bar_var, anchor="w", relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(5, 0))

        self.camera = cv2.VideoCapture(self.config.camera_index)
        if not self.camera.isOpened():
            self.status_var.set("Camera unavailable")

    def _build_emergency_buttons(self, parent):
        """Build emergency quick command buttons."""
        for idx, (pattern, phrase) in enumerate(self.quick_commands.items()):
            btn = ttk.Button(
                parent,
                text=f"{phrase}",
                command=lambda p=phrase: self.on_quick_command(p),
                style="Emergency.TButton"
            )
            btn.grid(row=idx, column=0, padx=5, pady=3, sticky="ew")
            
            # Show morse pattern on hover
            morse_label = ttk.Label(parent, text=f"Morse: {pattern}", font=("Consolas", 8), foreground="gray")
            morse_label.grid(row=idx, column=1, sticky="w", padx=(5, 0))

    def _build_morse_reference(self, parent):
        """Build the morse code reference chart."""
        # Letters
        letters_frame = ttk.LabelFrame(parent, text="Letters (A-Z)", padding=5)
        letters_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        letters = {k: v for k, v in self.morse_dict.items() if v.isalpha() and len(v) == 1}
        for idx, (morse, letter) in enumerate(sorted(letters.items(), key=lambda x: x[1])):
            row = idx // 2
            col = idx % 2
            text = f"{letter} = {morse}"
            ttk.Label(letters_frame, text=text, font=("Consolas", 9)).grid(
                row=row, column=col, sticky="w", padx=5, pady=2
            )

        # Numbers
        numbers_frame = ttk.LabelFrame(parent, text="Numbers (0-9)", padding=5)
        numbers_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        numbers = {k: v for k, v in self.morse_dict.items() if v.isdigit()}
        for idx, (morse, num) in enumerate(sorted(numbers.items(), key=lambda x: x[1])):
            row = idx // 2
            col = idx % 2
            text = f"{num} = {morse}"
            ttk.Label(numbers_frame, text=text, font=("Consolas", 9)).grid(
                row=row, column=col, sticky="w", padx=5, pady=2
            )

        # Common punctuation
        punctuation_frame = ttk.LabelFrame(parent, text="Punctuation", padding=5)
        punctuation_frame.grid(row=2, column=0, sticky="ew")
        
        common_punct = {
            ".-.-.-": ".",
            "--..--": ",",
            "..--..": "?",
            "-.-.--": "!",
        }
        for idx, (morse, punct) in enumerate(common_punct.items()):
            text = f"{punct} = {morse}"
            ttk.Label(punctuation_frame, text=text, font=("Consolas", 9)).grid(
                row=idx, column=0, sticky="w", padx=5, pady=2
            )

    def display_frame(self, frame):
        if frame is None:
            return
        frame_resized = cv2.resize(frame, (480, 360))
        rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    def set_status(
        self,
        blink_state: str,
        morse_buffer: str,
        translation: str,
        dotdash: str,
        ear_value: Optional[float] = None,
        mode: str = "IDLE",
        preview: str = "",
    ):
        self.blink_var.set(blink_state)
        self.morse_var.set(morse_buffer if morse_buffer else "...")
        self.translation_var.set(translation)
        self._update_translation_box(translation)
        self.status_var.set(dotdash if dotdash else "Ready")
        self.mode_var.set(mode.upper())
        self.preview_var.set(preview if preview else "—")
        
        if ear_value is not None:
            self.ear_var.set(max(0.0, min(1.0, ear_value)))
        self.status_bar_var.set(f"Mode: {mode.upper()} | Buffer: {morse_buffer if morse_buffer else 'empty'}")

    def copy_translation(self):
        text = self.translation_var.get()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_bar_var.set("✅ Copied translation to clipboard.")

    def _update_translation_box(self, text: str):
        self.translation_box.configure(state="normal")
        self.translation_box.delete("1.0", tk.END)
        self.translation_box.insert(tk.END, text)
        self.translation_box.configure(state="disabled")

    def teardown(self):
        if self.camera.isOpened():
            self.camera.release()
        self.root.destroy()

    def mainloop(self):
        self.root.mainloop()

    def clear_translation(self):
        self.translation_var.set("")
        self.translation_box.configure(state="normal")
        self.translation_box.delete("1.0", tk.END)
        self.translation_box.configure(state="disabled")
        self.status_bar_var.set("🗑 Cleared translation.")
