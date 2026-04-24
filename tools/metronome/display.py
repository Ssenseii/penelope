import sys
from colorama import Fore, Style

_LINES = 5  # total lines occupied by the display block


def init(beats_per_measure: int) -> None:
    """Print the initial (blank) display block."""
    beat_dots = "  " + " ".join("○" for _ in range(beats_per_measure))
    lines = [
        "  BPM: --- | Time: -/- | Beat: -",
        "",
        beat_dots,
        "",
        f"  {Style.DIM}[↑/↓] BPM  [A] Accent  [T] Tap Tempo  [Q] Quit{Style.RESET_ALL}",
    ]
    for line in lines:
        print(line)


def render(
    bpm: int,
    time_sig: tuple,
    current_beat: int,
    beats_per_measure: int,
    accent_enabled: bool,
    tap_mode: bool,
) -> None:
    sig_str = f"{time_sig[0]}/{time_sig[1]}"
    mode_str = (
        f"  {Fore.YELLOW}[TAP — press Space]{Style.RESET_ALL}" if tap_mode else ""
    )

    beats = []
    for i in range(1, beats_per_measure + 1):
        if i == current_beat:
            color = (Fore.GREEN + Style.BRIGHT) if (i == 1 and accent_enabled) else (Fore.CYAN + Style.BRIGHT)
            beats.append(f"{color}●{Style.RESET_ALL}")
        else:
            beats.append(f"{Style.DIM}○{Style.RESET_ALL}")

    bpm_str = f"{Fore.CYAN + Style.BRIGHT}{bpm}{Style.RESET_ALL}"
    beat_str = "  " + " ".join(beats)

    lines = [
        f"  BPM: {bpm_str} | Time: {sig_str} | Beat: {current_beat}{mode_str}",
        "",
        beat_str,
        "",
        f"  {Style.DIM}[↑/↓] BPM  [A] Accent  [T] Tap Tempo  [Q] Quit{Style.RESET_ALL}",
    ]

    # Move cursor up to the start of the display block, then overwrite each line
    sys.stdout.write(f"\033[{_LINES}A")
    for line in lines:
        sys.stdout.write(f"\033[2K{line}\n")
    sys.stdout.flush()
