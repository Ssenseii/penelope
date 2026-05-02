import os
import time
import datetime
import logging

import questionary
from colorama import Fore, Style

from tools.metronome import audio
from tools.chord_trainer.chords import CHORD_DATA, render_chord
from tools.chord_trainer.progression import LinearProgression, RandomProgression, CustomProgression
from tools.chord_trainer.scheduler import ChordScheduler
from tools.chord_trainer import display
from tools.chord_trainer.input_handler import InputHandler

_log = logging.getLogger(__name__)


class _State:
    def __init__(self, interval: float):
        self.interval = interval
        self.running = True
        self.paused = False
        self.skip_requested = False
        self.current_chord: str = ""
        self.next_chord: str = ""
        self.next_tick_at: float = 0.0
        self.chord_counts: dict[str, int] = {}
        self.total_paused: float = 0.0
        self._pause_start: float = 0.0


def _fmt_duration(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m > 0:
        return f"{m} min {s} sec"
    return f"{s} sec"


def _show_congrats(state: _State, active_secs: float) -> None:
    total = sum(state.chord_counts.values())
    dur = _fmt_duration(active_secs)
    print()
    print(Fore.CYAN + Style.BRIGHT + "  ╔" + "═" * 46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + f"  ║  Congrats! You spent {Fore.GREEN}{dur}{Fore.CYAN} training!{' ' * (22 - len(dur))}║")
    print(Fore.CYAN + Style.BRIGHT + f"  ║  {Fore.WHITE}{total} chord changes  •  {len(state.chord_counts)} chords practiced{Fore.CYAN}  ║")
    print(Fore.CYAN + Style.BRIGHT + "  ╚" + "═" * 46 + "╝")
    print()


def _log_session(state: _State, mode: str, start_dt: datetime.datetime, active_secs: float, selected: list[str]) -> None:
    bps = round(1.0 / state.interval, 3)
    bpm = round(60.0 / state.interval, 1)
    total = sum(state.chord_counts.values())
    paused_str = f"  (paused {_fmt_duration(state.total_paused)})" if state.total_paused >= 1 else ""

    sep = "─" * 52
    _log.info(sep)
    _log.info("CHORD TRAINING SESSION")
    _log.info("  Date       : %s", start_dt.strftime("%Y-%m-%d %H:%M:%S"))
    _log.info("  Duration   : %s%s", _fmt_duration(active_secs), paused_str)
    _log.info("  Mode       : %s", mode)
    _log.info("  Interval   : %.1f s/chord  →  BPS: %.3f  |  BPM: %.1f", state.interval, bps, bpm)
    _log.info("  Chords     : %s", ", ".join(selected))
    _log.info("  %s", sep)
    _log.info("  Chord Breakdown:")
    for chord in selected:
        count = state.chord_counts.get(chord, 0)
        _log.info("    %-4s ×  %d", chord, count)
    _log.info("  Total Changes : %d", total)
    _log.info(sep)


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
            questionary.Choice("Random",                       value="random"),
            questionary.Choice("Linear  (easiest → hardest)", value="linear"),
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
    state.chord_counts[state.current_chord] = 1
    state.next_chord = prog.next()
    state.next_tick_at = time.perf_counter() + interval

    def on_tick() -> None:
        audio.play(0.8)
        state.current_chord = state.next_chord
        state.next_chord = prog.next()
        state.chord_counts[state.current_chord] = state.chord_counts.get(state.current_chord, 0) + 1

    # --- Start subsystems ---
    scheduler = ChordScheduler(state, on_tick)
    handler = InputHandler(state)

    print()
    display.init()

    start_dt = datetime.datetime.now()
    start_time = time.perf_counter()

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

    end_time = time.perf_counter()
    if state.paused:
        state.total_paused += end_time - state._pause_start

    active_secs = max(0.0, end_time - start_time - state.total_paused)

    handler.stop()
    audio.cleanup()

    _show_congrats(state, active_secs)
    _log_session(state, mode, start_dt, active_secs, selected)
