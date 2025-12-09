## AI Eye-Blink Morse Code Translator — Mini Project Report

### Abstract
This mini-project builds an assistive communication system that interprets eye blinks as Morse code, converts decoded text into natural speech, and offers customizable shortcuts for urgent phrases. Leveraging OpenCV for video capture, MediaPipe Face Mesh for real-time blink detection, adaptive calibration, and a Tkinter interface, the platform empowers individuals with severe motor impairments to express themselves using only their eyes.

### Problem Definition
People with ALS, locked-in syndrome, or paralysis often retain limited eye control but lack reliable ways to communicate. Existing eye-tracking devices are expensive and require complex calibration. The challenge is to design a low-cost, camera-based application that robustly detects blinks, distinguishes dots/dashes, buffers Morse sequences, translates them to English, and produces speech output with minimal user effort.

### Objectives
- Deliver an accurate, real-time blink detector using MediaPipe Face Mesh landmarks and Eye Aspect Ratio (EAR) heuristics.
- Provide a calibration workflow that learns personalized thresholds for short/long blinks and inter-symbol gaps.
- Implement Morse buffering, decoding, quick command shortcuts, and English translation.
- Expose the functionality through a Tkinter GUI with live feed, status indicators, and text-to-speech controls.
- Evaluate latency, detection accuracy, and user effort; outline future enhancements for robustness and accessibility.

### Literature Review
1. **Assistive Communication via Eye Gazes (2000–2024):** Works like Das et al. (2020) rely on infrared eye trackers; they offer high accuracy but high cost. Our approach substitutes off-the-shelf webcams and computer vision to improve affordability.
2. **Blink Detection Algorithms:** Soukupová & Čech (2016) popularized EAR for blink detection. MediaPipe Face Mesh (Bazarevsky et al., 2020) provides lightweight neural estimation of facial landmarks, enabling hybrid ML + geometric approaches.
3. **Adaptive Interfaces for ALS:** Research from AAC (Augmentative and Alternative Communication) communities emphasizes personalization. We extend this with an automated calibration module that tunes blink thresholds and timing gaps per user.
4. **Morse Code Interfaces:** Morse-based input remains viable for constrained mobility. Prior systems often use mechanical switches; translating blink durations into Morse expands the modality to eye gestures.

### System Architecture
- **Sensors:** Standard webcam captures frames.
- **Vision Layer:** OpenCV feeds frames to MediaPipe Face Mesh to extract eye landmarks. Blink detector computes EAR, tracks openness, and measures blink durations.
- **Calibration Module:** Records baseline blinks, computes adaptive thresholds (short, long, symbol gap, letter gap).
- **Morse Decoder:** Buffers dots/dashes, segments letters/words, maps sequences to English, and handles quick-command patterns.
- **Interaction Layer:** Tkinter GUI displaying live feed, indicators, buffers, translations, and quick commands.
- **Output Layer:** Text-to-speech engine via `pyttsx3` or gTTS; optional auditory feedback.

### Block Diagram
1. Webcam input → 2. Frame preprocessing → 3. MediaPipe Face Mesh → 4. Blink detection & duration estimation → 5. Morse buffering and quick-command lookup → 6. English translation → 7. GUI display + TTS output.

### Architecture Diagram Narrative
- **Capture Node** routes frames to **Vision Processor**.
- **Vision Processor** sends blink events to **Calibration Manager** (during setup) or **Blink Classifier** (runtime).
- **Blink Classifier** emits dot/dash events to **Morse Buffer**.
- **Morse Buffer** communicates with **Decoder** and **Shortcut Engine** to produce text.
- **Text Stream** drives **GUI Renderer** and **TTS Synthesizer**.

### Module-Level Design
- `blink_detector.py`: Frame acquisition, EAR computation, blink state machine.
- `calibration.py`: Session-based learning of thresholds, persistence utilities.
- `morse_decoder.py`: Buffer management, Morse dictionary, quick commands.
- `tts_engine.py`: Unified wrapper over pyttsx3 and optional gTTS fallback.
- `gui.py`: Tkinter widgets, video canvas, control buttons, text areas.
- `utils.py`: Shared constants, timing helpers, configuration loading/saving.
- `main.py`: Application entrypoint, dependency wiring, event loop.

### Data Flow Diagram (DFD – Level 1)
User → Calibration Module → Thresholds → Blink Detector → Blink Events → Morse Decoder → English Text → GUI + TTS → User feedback loop.

### UML Summary
- **Use Case Diagram:** Actors: User, Caregiver. Use cases: Run calibration, communicate via blinks, trigger quick command, listen to speech output, review logs.
- **Activity Diagram:** Start → Calibrate → Capture frame → Detect blink → Classify dot/dash → Update buffer → Decode letter/word → Update GUI → Speak text → Loop or Stop.
- **Sequence Diagram:** `MainApp` requests frame from `CameraManager`; `BlinkDetector` publishes blink events to `MorseDecoder`; `MorseDecoder` notifies `GUIController`; `GUIController` invokes `TTSEngine` when user presses Speak.

### Methodology
1. **Data Acquisition:** Access webcam stream with OpenCV; convert to RGB for MediaPipe.
2. **Blink Detection:** Use MediaPipe landmarks to compute EAR for each eye, smooth using moving averages, and detect transitions between open/closed.
3. **Calibration:** Guide user through sample blinks, compute mean/standard deviation to set thresholds and inter-gap timings.
4. **Classification:** Measure blink duration; compare to thresholds to emit dot or dash events; track gaps using timers.
5. **Morse Decoding:** Append dots/dashes into buffer, detect letter/word boundaries via time gaps, map to dictionary, and handle quick commands.
6. **User Feedback:** Update GUI with statuses, sequences, translations; enable manual speech playback and quick-command testing.
7. **Evaluation:** Record detection accuracy, translation accuracy, latency, and user satisfaction metrics.

### Flowcharts & UML (Described)
- **Calibration Flowchart:** Start → Prompt user → Collect blink durations → Compute averages → Set thresholds → Save configuration → End.
- **Blink Detection Flowchart:** Start frame loop → Extract landmarks → Compute EAR → Determine state → If transition closed→open, measure duration → Classify dot/dash/gap → Update buffers → Continue.
- **Morse Decoding Activity:** On new symbol → Append to letter buffer → If gap exceeds `letter_gap`, decode letter → If gap exceeds `word_gap`, insert space → Update GUI/TTS.

### Technology Stack
- **Programming Language:** Python 3.10+
- **Computer Vision:** OpenCV, MediaPipe.
- **GUI:** Tkinter (standard library) with Pillow for image conversion.
- **Audio:** pyttsx3 (offline) with optional gTTS + playsound fallback.
- **Utilities:** NumPy, dataclasses, JSON for config persistence, threading for GUI-safe video loops.

### Evaluation Metrics
- Blink detection precision/recall (per-frame classification).
- Dot/dash classification accuracy vs. ground truth.
- Letter translation accuracy (decoded letters / intended letters).
- Communication latency (blink-to-speech time).
- User effort (number of blinks per word) and calibration success rate.

### Conclusion
The AI Eye-Blink Morse Code Translator unifies cost-effective vision-based blink detection, personalized calibration, Morse decoding, and text-to-speech output into a cohesive assistive tool. The modular design facilitates deployment on standard laptops, enabling individuals with motor impairments to communicate efficiently using existing hardware.

### Future Scope
- Integrate head pose compensation and eyelid open probability from neural models to improve robustness against lighting.
- Add online learning to adapt thresholds continuously.
- Port GUI to Streamlit/WebRTC for remote caregivers.
- Incorporate multilingual Morse dictionaries and predictive text suggestions.
- Embed telemetry for clinician review and integration with smart-home ecosystems.

### PPT Slides Outline
1. **Title & Motivation**
2. **Problem Statement & Target Users**
3. **Objectives**
4. **Related Work / Literature**
5. **System Architecture Overview**
6. **Blink Detection & Calibration**
7. **Morse Decoding Pipeline**
8. **GUI & User Experience**
9. **Quick Command Shortcuts**
10. **Text-to-Speech & Output Modalities**
11. **Evaluation Metrics & Results**
12. **Conclusion & Future Scope**
13. **Live Demo / Video Link**


