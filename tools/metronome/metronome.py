import os
import time

import questionary
from colorama import Fore, Style

from config.constants import (
    DEFAULT_TIME_SIGNATURE,
    ACCENT_ENABLED,
    BPM_PRESETS,
    MIN_BPM,
    MAX_BPM,
)
from tools.metronome import audio, display
from tools.metronome.engine import MetronomeEngine
from tools.metronome.input_handler import InputHandler


class _State:
    def __init__(self, bpm: int, time_sig: tuple):
        self.bpm = bpm
        self.time_sig = time_sig
        self.running = True
        self.accent_enabled = ACCENT_ENABLED
        self.tap_mode = False
        self.tap_times: list[float] = []
        self.tick_count = 0


def _find_mp3() -> str:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for candidate in [
        os.path.join(base, "assets", "metronome.mp3"),
        os.path.join(base, "metronome.mp3"),
    ]:
        if os.path.exists(candidate):
            return candidate
    return ""


def _select_bpm() -> int | None:
    choices = [questionary.Choice(str(b), value=b) for b in BPM_PRESETS]
    choices += [
        questionary.Choice("Custom…", value="custom"),
        questionary.Choice("Back",    value=None),
    ]

    result = questionary.select(
        "Select BPM:",
        choices=choices,
        style=questionary.Style([
            ("selected",    "fg:cyan bold"),
            ("pointer",     "fg:cyan bold"),
            ("highlighted", "fg:cyan"),
        ]),
    ).ask()

    if result is None:
        return None

    if result == "custom":
        raw = questionary.text(
            f"Enter BPM ({MIN_BPM}–{MAX_BPM}):",
            validate=lambda v: (
                True
                if v.strip().isdigit() and MIN_BPM <= int(v.strip()) <= MAX_BPM
                else f"Enter a whole number between {MIN_BPM} and {MAX_BPM}."
            ),
        ).ask()
        return int(raw.strip()) if raw is not None else None

    return result


def run() -> None:
    bpm = _select_bpm()
    if bpm is None:
        return

    state = _State(bpm, DEFAULT_TIME_SIGNATURE)
    beats_per_measure = DEFAULT_TIME_SIGNATURE[0]

    mp3_path = _find_mp3()
    audio_ok = audio.init(mp3_path) if mp3_path else False
    if not audio_ok:
        print(Fore.YELLOW + "  Warning: audio unavailable — running in silent mode." + Style.RESET_ALL)

    def on_tick() -> None:
        state.tick_count += 1
        current_beat = ((state.tick_count - 1) % beats_per_measure) + 1
        volume = 1.0 if (current_beat == 1 and state.accent_enabled) else 0.6
        audio.play(volume)
        display.render(
            state.bpm, state.time_sig, current_beat,
            beats_per_measure, state.accent_enabled, state.tap_mode,
        )

    print()
    display.init(beats_per_measure)

    engine = MetronomeEngine(state, on_tick)
    handler = InputHandler(state)

    engine.start()
    handler.start()

    try:
        while state.running:
            time.sleep(0.05)
    except KeyboardInterrupt:
        state.running = False

    handler.stop()
    audio.cleanup()
    print()
