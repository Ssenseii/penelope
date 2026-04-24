from colorama import Fore, Style

# (string_name, fret) — fret is int for played notes, "x" for muted
CHORD_DATA: dict[str, list[tuple[str, int | str]]] = {
    "C": [("e", 0), ("B", 1), ("G", 0), ("D", 2), ("A", 3), ("E", "x")],
    "A": [("e", 0), ("B", 2), ("G", 2), ("D", 2), ("A", 0), ("E", "x")],
    "G": [("e", 3), ("B", 3), ("G", 0), ("D", 0), ("A", 2), ("E", 3)],
    "D": [("e", 2), ("B", 3), ("G", 2), ("D", 0), ("A", "x"), ("E", "x")],
    "E": [("e", 0), ("B", 0), ("G", 1), ("D", 2), ("A", 2), ("E", 0)],
}


def render_chord(name: str) -> str:
    """
    Render a chord as a colored ASCII tab where each fret column aligns vertically.

    Example output for C major (max fret = 3):

      e|--0-----------
      B|-----1--------
      G|--0-----------
      D|--------2-----
      A|-----------3--
      E|--x-----------   (muted, in red)

    Each fret position occupies 3 characters (--N or ---).
    Numbers in the same fret column align across all strings.
    """
    strings = CHORD_DATA[name]
    numeric_frets = [f for _, f in strings if isinstance(f, int)]
    max_fret = max(numeric_frets) if numeric_frets else 0

    lines = []
    for string_name, fret in strings:
        segments = []
        for pos in range(max_fret + 1):
            if fret == "x" and pos == 0:
                segments.append(f"{Fore.RED + Style.BRIGHT}--x{Style.RESET_ALL}")
            elif fret == pos:
                segments.append(f"{Fore.CYAN + Style.BRIGHT}--{fret}{Style.RESET_ALL}")
            else:
                segments.append(f"{Style.DIM}---{Style.RESET_ALL}")
        segments.append(f"{Style.DIM}--{Style.RESET_ALL}")
        lines.append(
            f"{Fore.WHITE + Style.BRIGHT}{string_name}|{Style.RESET_ALL}"
            + "".join(segments)
        )

    return "\n".join(lines)
