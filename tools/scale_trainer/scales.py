from colorama import Fore, Style

CHROMATIC = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

# Semitone index of each open string (CHROMATIC where A=0)
_OPEN = {"E": 7, "A": 0, "D": 5, "G": 10, "B": 2, "e": 7}

# Low-to-high string order for ascending progression
_ASCENDING_ORDER = ["E", "A", "D", "G", "B", "e"]

# High-to-low string order for tab display (standard notation)
_DISPLAY_ORDER = ["e", "B", "G", "D", "A", "E"]

SCALE_INTERVALS: dict[str, list[int]] = {
    "minor": [0, 3, 5, 7, 10],
    "major": [0, 2, 4, 7, 9],
}

# (lo_offset, hi_offset) from root_fret_on_low_E for each of the 5 boxes
_BOX_OFFSETS: dict[str, list[tuple[int, int]]] = {
    "minor": [(0, 3), (2, 5), (4, 8), (7, 10), (9, 12)],
    "major": [(-1, 2), (1, 5), (3, 7), (6, 9), (9, 12)],
}


def get_scale_notes(root: str, scale_type: str) -> list[str]:
    root_idx = CHROMATIC.index(root)
    return [CHROMATIC[(root_idx + i) % 12] for i in SCALE_INTERVALS[scale_type]]


def _root_fret_on_e(root: str) -> int:
    return (CHROMATIC.index(root) - _OPEN["E"] + 12) % 12


def get_box_range(root: str, scale_type: str, box_num: int) -> tuple[int, int]:
    lo_off, hi_off = _BOX_OFFSETS[scale_type][box_num - 1]
    base = _root_fret_on_e(root)
    # Shift up an octave if lo_offset would produce a negative fret
    if base + lo_off < 0:
        base += 12
    return base + lo_off, base + hi_off


def get_box(root: str, scale_type: str, box_num: int) -> list[tuple[str, int, str]]:
    """Return (string_name, fret, note_name) positions sorted low-E to high-e, low fret first."""
    root_idx = CHROMATIC.index(root)
    scale_set = {(root_idx + i) % 12 for i in SCALE_INTERVALS[scale_type]}
    lo_fret, hi_fret = get_box_range(root, scale_type, box_num)

    positions = []
    for string_name in _ASCENDING_ORDER:
        open_idx = _OPEN[string_name]
        for fret in range(lo_fret, hi_fret + 1):
            if (open_idx + fret) % 12 in scale_set:
                note = CHROMATIC[(open_idx + fret) % 12]
                positions.append((string_name, fret, note))

    return positions


def render_tab(
    box_notes: list[tuple[str, int, str]],
    active_string: str,
    active_fret: int,
    min_fret: int,
    max_fret: int,
) -> str:
    col_w = max(3, len(str(max_fret)) + 2)

    lines = []
    for string_name in _DISPLAY_ORDER:
        fret_map = {fret for (s, fret, _) in box_notes if s == string_name}
        row = f"{Fore.WHITE + Style.BRIGHT}{string_name}|{Style.RESET_ALL}"
        for fret in range(min_fret, max_fret + 1):
            fret_str = str(fret)
            seg = "-" * (col_w - len(fret_str)) + fret_str
            if fret in fret_map:
                if string_name == active_string and fret == active_fret:
                    row += Fore.CYAN + Style.BRIGHT + seg + Style.RESET_ALL
                else:
                    row += Fore.WHITE + Style.DIM + seg + Style.RESET_ALL
            else:
                row += Style.DIM + "-" * col_w + Style.RESET_ALL
        row += Style.DIM + "--" + Style.RESET_ALL
        lines.append(row)

    return "\n".join(lines)
