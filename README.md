# Guitar Practice Tool

A terminal-based practice companion with a chord trainer and a metronome.

## Requirements

- Python 3.10+
- Windows (uses the `keyboard` library for global hotkeys)

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Tools

### Chord Trainer

Displays chord diagrams and cycles through them on a timer so you can practice switching.

- Select chords from the CAGED set (C, A, G, D, E)
- Choose a progression mode: **Linear**, **Random**, or **Custom** (enter your own sequence)
- Set the interval between changes (0.5–30 seconds)
- Controls during practice: `Space` pause · `→` skip · `Q` quit

### Metronome

High-precision click track using `time.perf_counter()` with anti-drift scheduling.

- Pick a BPM preset or enter a custom value (30–300)
- Controls during playback: `↑/↓` adjust BPM · `A` toggle accent · `T` tap tempo · `Q` quit

Requires `metronome.mp3` in the project root (included).
