## Additional Module Specification — Chord Switching Trainer (Primary Tool)

This module becomes the central practice feature, using the metronome engine as a timing backbone while focusing on chord transitions.

---

# 1. Overview

The **Chord Switching Trainer** guides users through timed transitions between major guitar chords:

* C, A, G, D, E (CAGED system)
* ASCII tab visualization
* Configurable interval (seconds per chord)
* Multiple progression modes:

  * Linear (ordered difficulty)
  * Random
  * Custom pattern
* Selectable chord subset
* Audible cue on each transition (via `metronome.mp3`)

---

# 2. Architecture Additions

### 2.1 Updated Structure

```plaintext
/tools/
├── metronome/
│   └── ...
├── chord_trainer/
│   ├── trainer.py
│   ├── progression.py
│   ├── chords.py
│   ├── display.py
│   └── scheduler.py
```

---

### 2.2 Responsibilities

* **trainer.py**

  * Entry point for chord trainer tool
  * Handles configuration flow and runtime loop

* **progression.py**

  * Generates chord sequences based on mode

* **chords.py**

  * Stores chord definitions (ASCII tabs)

* **display.py**

  * Renders chord diagrams and UI

* **scheduler.py**

  * Handles interval timing (built on metronome principles)

---

# 3. Chord Definitions

### 3.1 ASCII Representation

Each chord stored as structured text:

Example (C Major):

```id="0jz3vd"
C_MAJOR = """
e|--0--
B|--1--
G|--0--
D|--2--
A|--3--
E|--x--
"""
```

Define for:

* C Major
* A Major
* G Major
* D Major
* E Major

---

### 3.2 Data Structure

```python id="w1u0r8"
CHORDS = {
    "C": C_MAJOR,
    "A": A_MAJOR,
    "G": G_MAJOR,
    "D": D_MAJOR,
    "E": E_MAJOR,
}
```

---

# 4. Functional Requirements

## 4.1 Chord Selection

Using `questionary.checkbox`:

* User selects subset of chords
* Default: all selected

Constraint:

* Minimum 2 chords required

---

## 4.2 Interval Configuration

Prompt:

* "Seconds between chord changes"
* Accept float or integer
* Validate (e.g., 0.5s – 30s)

---

## 4.3 Progression Modes

### 4.3.1 Linear Mode

Fixed order (easiest → hardest):

```id="5xhb82"
["A", "E", "D", "C", "G"]
```

Filtered to selected chords only.

---

### 4.3.2 Random Mode

* Random selection from chosen chords
* Avoid immediate repetition if possible

---

### 4.3.3 Custom Pattern

User inputs sequence:

Example:

```id="lfvtg1"
C G A D
```

Validation:

* Only selected chords allowed
* Must contain ≥2 entries

---

## 4.4 Scheduler (Core Timing)

### Behavior

* Runs loop with fixed interval (seconds)
* On each tick:

  1. Play metronome sound
  2. Advance chord
  3. Update display

### Timing Strategy

Reuse precision approach from metronome:

```id="0s9ksp"
next_tick = now + interval
```

* Use `time.perf_counter()`
* Avoid drift accumulation

---

## 4.5 Audio Cue

* Trigger `metronome.mp3` once per chord change
* Acts as transition marker (not continuous beat)

---

## 4.6 Display

### Example Output

```id="ow28qi"
Next chord in: 3.0s

Current: C

e|--0--
B|--1--
G|--0--
D|--2--
A|--3--
E|--x--

Upcoming: G
```

### Behavior

* Show:

  * Current chord (large emphasis)
  * Next chord (preview)
  * Countdown timer (optional but recommended)

### Refresh

* Update every ~100ms for countdown
* Full redraw on chord change

---

## 4.7 Controls

| Key     | Action             |
| ------- | ------------------ |
| Space   | Pause / Resume     |
| → Arrow | Skip to next chord |
| Q       | Quit session       |

---

# 5. User Flow

## 5.1 Entry

1. Run CLI
2. Select: "Chord Trainer"

---

## 5.2 Setup

1. Select chords (checkbox)
2. Choose progression mode:

   * Linear
   * Random
   * Custom
3. If custom → input pattern
4. Set interval (seconds)

---

## 5.3 Runtime

* Display first chord immediately
* Start countdown
* On each interval:

  * Play sound
  * Switch chord
  * Update UI

---

# 6. Integration with Metronome

### Shared Components

* Audio playback (`audio.py`)
* Timing logic pattern (not necessarily same thread)

### Design Choice

Do **not** run full metronome loop simultaneously.
Instead:

* Use metronome sound as a **transition cue only**

---

# 7. Progression Engine

### Interface

```python id="5g95is"
class Progression:
    def next(self) -> str:
        pass
```

### Implementations

* `LinearProgression`
* `RandomProgression`
* `CustomProgression`

---

# 8. Edge Cases

* Only 1 chord selected → reject
* Invalid custom pattern → re-prompt
* Extremely low interval (<0.5s) → warn about usability
* Audio lag → does not block chord switching

---

# 9. Extensibility

Future enhancements:

* Minor chords
* Barre chord variations
* Difficulty scaling (auto speed increase)
* Practice statistics (time spent, accuracy tracking)
* Visual fretboard instead of tabs

---

# 10. Relationship Between Tools

| Tool          | Role                      |
| ------------- | ------------------------- |
| Metronome     | Standalone timing tool    |
| Chord Trainer | Primary practice workflow |

The chord trainer internally reuses timing and audio concepts but remains logically independent.
