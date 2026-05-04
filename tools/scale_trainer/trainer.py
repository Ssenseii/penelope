import os
import time
import datetime
import logging

import questionary
from colorama import Fore, Style

from tools.metronome import audio
from tools.scale_trainer.scales import CHROMATIC, get_scale_notes, get_box, get_box_range, render_tab
from tools.scale_trainer.progression import (
    AscendingProgression, DescendingProgression, RandomProgression, CustomProgression,
)
from tools.scale_trainer.scheduler import ScaleScheduler
from tools.scale_trainer import display
from tools.scale_trainer.input_handler import InputHandler

_log = logging.getLogger(__name__)

_STYLE = questionary.Style([
    ("selected",    "fg:cyan bold"),
    ("pointer",     "fg:cyan bold"),
    ("highlighted", "fg:cyan"),
    ("checked",     "fg:green bold"),
])


class _State:
    def __init__(self, interval: float):
        self.interval = interval
        self.running = True
        self.paused = False
        self.skip_requested = False
        self.current_note: str = ""
        self.current_string: str = ""
        self.current_fret: int = 0
        self.next_note: str = ""
        self.next_string: str = ""
        self.next_fret: int = 0
        self.next_tick_at: float = 0.0
        self.note_counts: dict[str, int] = {}
        self.total_paused: float = 0.0
        self._pause_start: float = 0.0


def _fmt_duration(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m > 0:
        return f"{m} min {s} sec"
    return f"{s} sec"


def _show_congrats(state: _State, active_secs: float) -> None:
    total = sum(state.note_counts.values())
    dur = _fmt_duration(active_secs)
    notes_count = len(state.note_counts)
    dur_pad = " " * max(0, 14 - len(dur))
    note_pad = " " * max(0, 10 - len(str(total)) - len(str(notes_count)))
    print()
    print(Fore.CYAN + Style.BRIGHT + "  ╔" + "═" * 46 + "╗")
    print(Fore.CYAN + Style.BRIGHT + f"  ║  Congrats! You spent {Fore.GREEN}{dur}{Fore.CYAN} training!{dur_pad}║")
    print(Fore.CYAN + Style.BRIGHT + f"  ║  {Fore.WHITE}{total} note changes  •  {notes_count} notes practiced{Fore.CYAN}{note_pad}║")
    print(Fore.CYAN + Style.BRIGHT + "  ╚" + "═" * 46 + "╝")
    print()


def _log_session(
    state: _State,
    scale_name: str,
    box_num: int,
    mode: str,
    start_dt: datetime.datetime,
    active_secs: float,
) -> None:
    bps = round(1.0 / state.interval, 3)
    bpm = round(60.0 / state.interval, 1)
    total = sum(state.note_counts.values())
    paused_str = f"  (paused {_fmt_duration(state.total_paused)})" if state.total_paused >= 1 else ""

    sep = "─" * 52
    _log.info(sep)
    _log.info("SCALE TRAINING SESSION")
    _log.info("  Date       : %s", start_dt.strftime("%Y-%m-%d %H:%M:%S"))
    _log.info("  Duration   : %s%s", _fmt_duration(active_secs), paused_str)
    _log.info("  Scale      : %s", scale_name)
    _log.info("  Box        : Box %d", box_num)
    _log.info("  Mode       : %s", mode)
    _log.info("  Interval   : %.1f s/note  →  BPS: %.3f  |  BPM: %.1f", state.interval, bps, bpm)
    _log.info("  %s", sep)
    _log.info("  Note Breakdown:")
    for note, count in sorted(state.note_counts.items()):
        _log.info("    %-3s ×  %d", note, count)
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
        return "Enter a number (e.g. 2 or 1.5)."
    if f < 0.5 or f > 30:
        return "Interval must be between 0.5 and 30 seconds."
    return True


def _validate_custom_pattern(v: str, scale_notes: list[str]) -> bool | str:
    tokens = v.strip().upper().split()
    if len(tokens) < 2:
        return "Enter at least 2 notes."
    invalid = [t for t in tokens if t not in scale_notes]
    if invalid:
        return f"Not in scale: {', '.join(invalid)}. Valid notes: {', '.join(scale_notes)}"
    return True


def run() -> None:
    # --- Root note ---
    root = questionary.select(
        "Root note:",
        choices=[questionary.Choice(n, value=n) for n in CHROMATIC],
        style=_STYLE,
    ).ask()
    if root is None:
        return

    # --- Scale type ---
    scale_type = questionary.select(
        "Scale type:",
        choices=[
            questionary.Choice("Minor Pentatonic", value="minor"),
            questionary.Choice("Major Pentatonic", value="major"),
        ],
        style=_STYLE,
    ).ask()
    if scale_type is None:
        return

    scale_notes = get_scale_notes(root, scale_type)
    scale_name = f"{root} {'Minor' if scale_type == 'minor' else 'Major'} Pentatonic"

    # --- Box position ---
    box_choices = []
    for i in range(1, 6):
        lo, hi = get_box_range(root, scale_type, i)
        box_choices.append(questionary.Choice(f"Box {i}  (frets {lo}–{hi})", value=i))
    box_choices.append(questionary.Choice("Back", value=None))

    box_num = questionary.select(
        "Box position:",
        choices=box_choices,
        style=_STYLE,
    ).ask()
    if box_num is None:
        return

    positions = get_box(root, scale_type, box_num)
    lo_fret, hi_fret = get_box_range(root, scale_type, box_num)

    # --- Progression mode ---
    mode = questionary.select(
        "Progression mode:",
        choices=[
            questionary.Choice("Ascending",      value="ascending"),
            questionary.Choice("Descending",     value="descending"),
            questionary.Choice("Random",         value="random"),
            questionary.Choice("Custom pattern", value="custom"),
            questionary.Choice("Back",           value=None),
        ],
        style=_STYLE,
    ).ask()
    if mode is None:
        return

    # --- Custom pattern input ---
    custom_positions: list[tuple[str, int, str]] = []
    if mode == "custom":
        # Map each note name to its first occurrence in the box (ascending order)
        note_to_pos: dict[str, tuple[str, int, str]] = {}
        for pos in positions:
            if pos[2] not in note_to_pos:
                note_to_pos[pos[2]] = pos

        raw = questionary.text(
            f"Enter note pattern from scale ({', '.join(scale_notes)}):",
            validate=lambda v: _validate_custom_pattern(v, scale_notes),
        ).ask()
        if raw is None:
            return
        custom_positions = [note_to_pos[n] for n in raw.strip().upper().split()]

    # --- Interval ---
    raw_interval = questionary.text(
        "Seconds per note (0.5 – 30):",
        default="2",
        validate=_validate_interval,
    ).ask()
    if raw_interval is None:
        return
    interval = float(raw_interval.strip())

    # --- Build progression ---
    if mode == "ascending":
        prog = AscendingProgression(positions)
    elif mode == "descending":
        prog = DescendingProgression(positions)
    elif mode == "random":
        prog = RandomProgression(positions)
    else:
        prog = CustomProgression(custom_positions)

    # --- Audio ---
    mp3_path = _find_mp3()
    audio_ok = audio.init(mp3_path) if mp3_path else False
    if not audio_ok:
        print(Fore.YELLOW + "  Warning: audio unavailable — silent mode." + Style.RESET_ALL)

    # --- State ---
    state = _State(interval)

    def _set_current(pos: tuple[str, int, str]) -> None:
        state.current_string, state.current_fret, state.current_note = pos

    def _set_next(pos: tuple[str, int, str]) -> None:
        state.next_string, state.next_fret, state.next_note = pos

    _set_current(prog.next())
    state.note_counts[state.current_note] = 1
    _set_next(prog.next())
    state.next_tick_at = time.perf_counter() + interval

    def on_tick() -> None:
        audio.play(0.8)
        _set_current((state.next_string, state.next_fret, state.next_note))
        state.note_counts[state.current_note] = state.note_counts.get(state.current_note, 0) + 1
        _set_next(prog.next())

    # --- Start subsystems ---
    scheduler = ScaleScheduler(state, on_tick)
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
            tab = render_tab(positions, state.current_string, state.current_fret, lo_fret, hi_fret)
            display.render(
                state.current_note,
                state.current_string,
                state.current_fret,
                state.next_note,
                state.next_string,
                state.next_fret,
                tab,
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
    _log_session(state, scale_name, box_num, mode, start_dt, active_secs)
