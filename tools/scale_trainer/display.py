import sys
from colorama import Fore, Style

_LINES = 14


def init() -> None:
    for _ in range(_LINES):
        print()


def render(
    current_note: str,
    current_string: str,
    current_fret: int,
    next_note: str,
    next_string: str,
    next_fret: int,
    tab: str,
    countdown: float | None,
    paused: bool,
) -> None:
    if paused:
        timer_str = f"  {Fore.YELLOW + Style.BRIGHT}PAUSED{Style.RESET_ALL}"
    elif countdown is not None:
        timer_str = f"  Next note in: {Fore.CYAN + Style.BRIGHT}{countdown:.1f}s{Style.RESET_ALL}"
    else:
        timer_str = "  Next note in: --"

    tab_lines = tab.strip().split("\n")
    while len(tab_lines) < 6:
        tab_lines.append("")
    colored_tab = [f"  {line}" for line in tab_lines]

    lines = [
        timer_str,
        "",
        f"  Current: {Fore.GREEN + Style.BRIGHT}{current_note}{Style.RESET_ALL}  ({current_string} string, fret {current_fret})",
        "",
        *colored_tab,
        "",
        f"  Upcoming: {Fore.CYAN + Style.BRIGHT}{next_note}{Style.RESET_ALL}  ({next_string} string, fret {next_fret})",
        "",
        f"  {Style.DIM}[Space] Pause  [→] Skip  [Q] Quit{Style.RESET_ALL}",
    ]

    sys.stdout.write(f"\033[{_LINES}A")
    for line in lines:
        sys.stdout.write(f"\033[2K{line}\n")
    sys.stdout.flush()
