## Module Specification — Pentatonic Scale Trainer

Helps users practice any pentatonic scale at their own tempo by cycling through the scale's notes one at a time, displaying each note's fretboard position and a countdown to the next.

---

# 1. Overview

The **Pentatonic Scale Trainer** guides users through the notes of a chosen pentatonic scale at a user-set tempo:

* Choose any root note (A – G, with sharps)
* Choose scale type: Major or Minor pentatonic
* Choose a fretboard position (Box 1 – Box 5)
* Set interval (seconds per note)
* Display shows current note name, its fretboard position as a tab snippet, the upcoming note, and a countdown
* Audible cue on each note transition (via `metronome.mp3`)
* Progression modes: Ascending, Descending, Random, Custom

---

# 2. Architecture

### 2.1 Structure

```plaintext
/tools/
├── metronome/
│   └── ...
├── chord_trainer/
│   └── ...
├── scale_trainer/
│   ├── __init__.py
│   ├── trainer.py
│   ├── scales.py
│   ├── progression.py
│   ├── display.py
│   └── scheduler.py
```

---

### 2.2 Responsibilities

* **trainer.py** — Entry point; handles config flow and runtime loop
* **scales.py** — Scale definitions and fretboard position data; note rendering
* **progression.py** — Generates note sequences based on mode
* **display.py** — Renders tab snippet and UI
* **scheduler.py** — Interval timing (mirrors `chord_trainer/scheduler.py`)

---

# 3. Scale Definitions

### 3.1 Pentatonic Intervals

| Type  | Intervals (semitones from root) |
| ----- | ------------------------------- |
| Minor | 0, 3, 5, 7, 10                  |
| Major | 0, 2, 4, 7, 9                   |

Both scales produce 5 distinct notes (hence "penta").

---

### 3.2 Root Notes

All 12 chromatic roots supported, using sharps only for simplicity:

```
A  A#  B  C  C#  D  D#  E  F  F#  G  G#
```

---

### 3.3 Fretboard Positions (Boxes)

The 5 pentatonic box patterns tile the neck. Each box is defined relative to the root position. Box 1 is the most common starting point (root on low E string).

For each box, every note in the scale is mapped to a `(string, fret)` occurrence. A scale has 5 notes × 2 occurrences per string × 6 strings = ~12 positions across the box.

**Data structure:**

```python
NOTE_DATA: dict[str, list[tuple[str, int]]] = {
    "A": [("E", 5), ("D", 7), ("B", 5)],   # all fret positions for note A
    "C": [("A", 3), ("G", 5)],
    ...
}
```

Each entry in the trainer cycle is one `(note_name, string, fret)` occurrence, ordered by the box pattern (low E → high e, ascending fret within each string).

---

### 3.4 Tab Rendering

The full box pattern is always visible — all note positions in the box are shown on every string. The current active note position is highlighted; all other positions in the box are shown dimmed so the player can see the full shape at a glance.

Example — A Minor Pentatonic Box 1, active note is A on E string fret 5:

```
  fret:  5    6    7    8
  e|----5---------8----
  B|----5---------8----
  G|----5----7---------
  D|----5----7---------
  A|----5----7---------
  E|----5---------8----
```

Each fret number occupies a fixed-width column aligned to its actual fret position. Fret 7 and fret 8 are always in separate columns — a note at fret 7 and a note at fret 8 never share a column even if they are on adjacent strings.

Rendering rules:

* **Active position** (`current_note` at its current `string` + `fret`) → `Fore.CYAN + Style.BRIGHT`
* **Other box positions** (same box, different string/fret) → `Fore.WHITE + Style.DIM`
* **Empty fret slots** (no note there) → `Style.DIM` dashes only

The tab spans from `min_fret` to `max_fret` of the box, with each fret slot rendered as a fixed-width segment (e.g. `--N` or `---`), identical to the column-alignment approach in `chord_trainer/chords.py`.

---

# 4. Functional Requirements

## 4.1 Configuration Flow

1. **Root note** — `questionary.select` from 12 chromatic options
2. **Scale type** — Major or Minor
3. **Box position** — Box 1 through Box 5 (labeled with starting fret for clarity)
4. **Progression mode** — Ascending, Descending, Random, Custom
5. **Custom pattern** (if selected) — user enters note names from the scale (e.g. `A C D E G`)
6. **Interval** — float, 0.5 – 30 seconds, default `2`

---

## 4.2 Progression Modes

### 4.2.1 Ascending

Cycle through all note occurrences in the box from low E to high e, low fret to high fret. Loops continuously.

### 4.2.2 Descending

Same as ascending but reversed (high e → low E). Loops continuously.

### 4.2.3 Random

Pick a random note occurrence from the box on each tick; avoid immediate repeats when possible.

### 4.2.4 Custom

User enters a space-separated sequence of note names from the scale (e.g. `A C D E G A`). Only note names valid for the chosen scale are accepted. Loops continuously.

---

## 4.3 Display

### Example Output

```
  Next note in: 1.8s

  Current: A  (E string, fret 5)

  e|----5---------8----
  B|----5---------8----
  G|----5----7---------
  D|----5----7---------
  A|----5----7---------
  E|----5---------8----
        ^ active

  Upcoming: C  (A string, fret 3)

  [Space] Pause  [→] Skip  [Q] Quit
```

The full box pattern is always visible. Only the active position (cyan, bright) changes each tick; the rest of the box stays dim-white, giving the player constant spatial context.

### Behavior

* Refresh every ~100ms for smooth countdown
* In-place redraw using ANSI cursor-up (same technique as `chord_trainer/display.py`)
* Fixed line count to prevent scroll jitter

---

## 4.4 Controls

| Key     | Action             |
| ------- | ------------------ |
| Space   | Pause / Resume     |
| → Arrow | Skip to next note  |
| Q       | Quit session       |

---

## 4.5 Session Summary & Logging

On quit, print a summary box and write a structured log entry:

```
  ╔══════════════════════════════════════════════╗
  ║  Congrats! You spent 4 min 12 sec training!  ║
  ║  47 note changes  •  5 notes practiced       ║
  ╚══════════════════════════════════════════════╝
```

Log entry fields:

* Date / time
* Duration (active, minus paused time)
* Scale (e.g. `A Minor Pentatonic`)
* Box position
* Progression mode
* Interval (s/note, BPS, BPM equivalent)
* Per-note hit count
* Total note changes

---

# 5. User Flow

1. Main menu → select **Scale Trainer**
2. Pick root note → scale type → box → mode → interval
3. Trainer starts: first note displayed immediately, countdown begins
4. On each tick: sound plays, next note shown, display updates
5. User presses Q (or Ctrl+C) → summary printed → log written → return to main menu

---

# 6. State Model

```python
class _State:
    interval: float
    running: bool
    paused: bool
    skip_requested: bool
    current_note: str          # e.g. "A"
    current_pos: tuple[str, int]  # (string_name, fret)
    next_note: str
    next_pos: tuple[str, int]
    next_tick_at: float
    note_counts: dict[str, int]
    total_paused: float
    _pause_start: float
```

---

# 7. Integration with Main Menu

Add a third entry to `main.py`:

```python
questionary.Choice("Scale Trainer", value="scale_trainer")
```

Route to `tools.scale_trainer.trainer.run`.

---

# 8. Shared Components

| Component         | Source                          |
| ----------------- | ------------------------------- |
| Audio playback    | `tools.metronome.audio`         |
| Scheduler pattern | mirrors `chord_trainer/scheduler.py` |
| Input handler     | mirrors `chord_trainer/input_handler.py` |

The scheduler and input handler can be copied verbatim or lightly renamed — the state interface is identical.

---

# 9. Edge Cases

* Root + box combination that produces frets < 0 → clamp to open string or skip that occurrence
* Custom pattern with note not in chosen scale → re-prompt with clear error
* Interval < 0.5s → reject with validation message
* Audio unavailable → silent mode, continue normally

---

# 10. Extensibility

* Full-neck mode (all 5 boxes linked, cycle through entire neck)
* Two-notes-per-string display (show a whole string's pair simultaneously)
* Speed ramp (auto-increase interval after N loops)
* Scale comparison mode (major vs minor side-by-side)
* Support for other 5-note scales (blues scale, etc.)
