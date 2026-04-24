# Guitar Practice CLI Tool – Metronome Module Specification

## 1. Overview

This module implements a high-precision, interactive metronome as the first tool within an existing Python CLI application. It is designed for cross-platform use (Windows, Linux, macOS) and runs via:

```
python main.py
```

The metronome provides:

* Configurable BPM (preset + custom)
* Real-time tempo adjustment via keyboard
* Accurate timing with minimal drift
* Audio playback using `metronome.mp3`
* Time signatures (default: 4/4)
* Beat accents
* Visual feedback in the terminal
* Tap tempo input

---

## 2. Architecture

### 2.1 Module Structure

```
/project-root
│
├── main.py
├── config/
│   └── constants.py
├── tools/
│   └── metronome/
│       ├── metronome.py
│       ├── engine.py
│       ├── audio.py
│       ├── input_handler.py
│       └── display.py
├── assets/
│   └── metronome.mp3
```

---

### 2.2 Responsibilities

* **main.py**

  * Entry point
  * Uses CLI framework (e.g., questionary) to select tools

* **metronome.py**

  * Orchestrates user interaction and lifecycle

* **engine.py**

  * Handles timing loop and scheduling
  * Ensures precision (core logic)

* **audio.py**

  * Plays `metronome.mp3` on each tick

* **input_handler.py**

  * Captures real-time keyboard input (non-blocking)

* **display.py**

  * CLI rendering (tempo, beat, measure, visual cues)

* **constants.py**

  * Stores presets and defaults

---

## 3. Configuration

### 3.1 constants.py

```python
DEFAULT_BPM = 80

BPM_PRESETS = [
    60, 70, 80, 90, 100, 110, 120, 140, 160
]

MIN_BPM = 30
MAX_BPM = 300

DEFAULT_TIME_SIGNATURE = (4, 4)

ACCENT_ENABLED = True

TAP_TEMPO_SAMPLE_SIZE = 4
```

---

## 4. Functional Requirements

### 4.1 BPM Selection

* User selects BPM via:

  * Preset menu (questionary select)
  * Custom numeric input

* Validation:

  * Must be within `[MIN_BPM, MAX_BPM]`

---

### 4.2 Timing Engine

#### Approach

* Use `time.perf_counter()` for high-resolution timing
* Avoid `time.sleep()` drift by:

  * Scheduling next tick based on absolute time
  * Compensating for execution delay

#### Interval Calculation

```
interval = 60 / BPM
```

#### Execution Loop

* Maintain `next_tick_time`
* On each loop:

  * Wait until `next_tick_time`
  * Trigger audio + visual update
  * Increment `next_tick_time += interval`

---

### 4.3 Audio Playback

#### Strategy

* Play sound per beat (not looping audio file)
* Each tick triggers playback

#### Requirements

* Non-blocking playback
* Minimal latency

#### Suggested Libraries

* `simpleaudio` (preferred for low-latency, cross-platform)
* Fallback: `playsound` (less precise)

---

### 4.4 Real-Time Controls

#### Input Method

* Non-blocking keyboard listener (e.g., `keyboard` or `curses`)

#### Key Bindings

| Key     | Action                  |
| ------- | ----------------------- |
| ↑ Arrow | Increase BPM (+1 or +5) |
| ↓ Arrow | Decrease BPM            |
| A       | Toggle accent           |
| T       | Tap tempo mode          |
| Q       | Quit metronome          |

---

### 4.5 Tap Tempo

#### Behavior

* User presses `T` to enter tap mode
* Then taps a key (e.g., spacebar) repeatedly

#### Calculation

* Record timestamps of last N taps
* Compute average interval:

```
avg_interval = mean(diff between taps)
BPM = 60 / avg_interval
```

* Update BPM dynamically

---

### 4.6 Time Signature

* Default: 4/4
* Each measure tracks beat count

#### Beat Tracking

```
current_beat = (tick_count % beats_per_measure) + 1
```

---

### 4.7 Accents

* First beat of each measure is accented

#### Implementation Options

1. **Preferred**: Slightly louder playback (if library supports volume)
2. **Fallback**: Play sound twice quickly or add visual emphasis

---

### 4.8 Visual Feedback

#### CLI Output (updated per tick)

Example:

```
BPM: 120 | Time: 4/4 | Beat: 1

> ● ○ ○ ○
```

* `●` = accented beat
* `○` = normal beats

#### Color (via colorama)

* Accented beat: bright/green
* Others: dim/white

#### Refresh Strategy

* Clear line and redraw (avoid full screen flicker)

---

## 5. User Flow

### 5.1 Entry

1. Run `python main.py`
2. Select "Metronome" from tool list

### 5.2 Configuration

1. Choose BPM:

   * Preset list OR
   * Custom input

2. Confirm settings

### 5.3 Runtime

* Metronome starts immediately
* User can:

  * Adjust BPM live
  * Toggle accent
  * Use tap tempo
  * Quit anytime

---

## 6. Precision Considerations

* Use monotonic clock (`perf_counter`)
* Avoid cumulative drift by:

  * Not relying solely on sleep duration
* Keep audio playback lightweight
* Separate timing and input handling threads

---

## 7. Concurrency Model

### Threads

* **Main thread**: UI + orchestration
* **Timing thread**: metronome engine loop
* **Input thread**: keyboard listener

### Communication

* Shared state object:

  * BPM
  * running flag
  * accent enabled
  * tap tempo buffer

* Use thread-safe primitives (Lock if needed)

---

## 8. Error Handling

* Invalid BPM input → prompt retry
* Audio failure → fallback to silent mode with warning
* Keyboard listener failure → disable live controls gracefully

---

## 9. Extensibility

Future features should plug into this structure:

* Subdivisions (e.g., eighth notes)
* Multiple sound samples
* Practice routines (tempo ramping)
* Pattern-based rhythms

