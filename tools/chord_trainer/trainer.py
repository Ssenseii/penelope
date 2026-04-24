import os
import time

import questionary
from colorama import Fore, Style

from tools.metronome import audio
from tools.chord_trainer.chords import CHORD_DATA, render_chord
from tools.chord_trainer.progression import LinearProgression, RandomProgression, CustomProgression
from tools.chord_trainer.scheduler import ChordScheduler
from tools.chord_trainer import display
from tools.chord_trainer.input_handler import InputHandler


class _State:
    def __init__(self, interval: float):
        self.interval = interval
        self.running = True
        self.paused = False
        self.skip_requested = False
        self.current_chord: str = ""
        self.next_chord: str = ""
        self.next_tick_at: float = 0.0


def _find_mp3() -> str:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for candidate in [
        os.path.join(base, "assets", "metronome.mp3"),
        os.path.join(base, "metronome.mp3"),
    ]:
        if os.path.exists(candidate):
            return candidate
    return ""


def _validate_interval(v: str) -> bool | str:
    try:
        f = float(v.strip())
    except ValueError:
        return "Enter a number (e.g. 4 or 2.5)."
    if f < 0.5 or f > 30:
        return "Interval must be between 0.5 and 30 seconds."
    return True


def _validate_pattern(v: str, selected: list[str]) -> bool | str:
    tokens = v.strip().upper().split()
    if len(tokens) < 2:
        return "Enter at least 2 chords."
    invalid = [t for t in tokens if t not in selected]
    if invalid:
        return f"Not in your selection: {', '.join(invalid)}"
    return True


def run() -> None:
    # --- Chord selection ---
    while True:
        selected = questionary.checkbox(
            "Select chords to practice (Space to toggle, Enter to confirm):",
            choices=[questionary.Choice(name, checked=True) for name in CHORD_DATA],
            style=questionary.Style([
                ("selected",    "fg:cyan bold"),
                ("pointer",     "fg:cyan bold"),
                ("highlighted", "fg:cyan"),
                ("checked",     "fg:green bold"),
            ]),
        ).ask()
        if selected is None:
            return
        if len(selected) >= 2:
            break
        print(Fore.RED + Style.BRIGHT + "  ✗  Select at least 2 chords." + Style.RESET_ALL)

    # --- Progression mode ---
    mode = questionary.select(
        "Progression mode:",
        choices=[
            questionary.Choice("Linear  (easiest → hardest)", value="linear"),
            questionary.Choice("Random",                       value="random"),
            questionary.Choice("Custom pattern",               value="custom"),
            questionary.Choice("Back",                         value=None),
        ],
        style=questionary.Style([
            ("selected",    "fg:cyan bold"),
            ("pointer",     "fg:cyan bold"),
            ("highlighted", "fg:cyan"),
        ]),
    ).ask()
    if mode is None:
        return

    # --- Custom pattern input ---
    pattern: list[str] = []
    if mode == "custom":
        raw = questionary.text(
            f"Enter pattern using selected chords (e.g. C G A D):",
            validate=lambda v: _validate_pattern(v, selected),
        ).ask()
        if raw is None:
            return
        pattern = raw.strip().upper().split()

    # --- Interval ---
    raw_interval = questionary.text(
        "Seconds per chord (0.5 – 30):",
        default="4",
        validate=_validate_interval,
    ).ask()
    if raw_interval is None:
        return
    interval = float(raw_interval.strip())

    # --- Build progression ---
    if mode == "linear":
        prog = LinearProgression(selected)
    elif mode == "random":
        prog = RandomProgression(selected)
    else:
        prog = CustomProgression(pattern)

    # --- Audio ---
    mp3_path = _find_mp3()
    audio_ok = audio.init(mp3_path) if mp3_path else False
    if not audio_ok:
        print(Fore.YELLOW + "  Warning: audio unavailable — silent mode." + Style.RESET_ALL)

    # --- State ---
    state = _State(interval)
    state.current_chord = prog.next()
    state.next_chord = prog.next()
    state.next_tick_at = time.perf_counter() + interval

    def on_tick() -> None:
        audio.play(0.8)
        state.current_chord = state.next_chord
        state.next_chord = prog.next()

    # --- Start subsystems ---
    scheduler = ChordScheduler(state, on_tick)
    handler = InputHandler(state)

    print()
    display.init()

    scheduler.start()
    handler.start()

    try:
        while state.running:
            now = time.perf_counter()
            countdown = max(0.0, state.next_tick_at - now) if not state.paused else None
            display.render(
                state.current_chord,
                state.next_chord,
                render_chord(state.current_chord),
                countdown,
                state.paused,
            )
            time.sleep(0.1)
    except KeyboardInterrupt:
        state.running = False

    handler.stop()
    audio.cleanup()
    print()
