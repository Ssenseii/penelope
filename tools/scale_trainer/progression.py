import random

# All progression classes consume and produce (string_name, fret, note_name) tuples.


class AscendingProgression:
    def __init__(self, positions: list[tuple[str, int, str]]):
        self._positions = positions
        self._index = 0

    def next(self) -> tuple[str, int, str]:
        pos = self._positions[self._index]
        self._index = (self._index + 1) % len(self._positions)
        return pos


class DescendingProgression:
    def __init__(self, positions: list[tuple[str, int, str]]):
        self._positions = list(reversed(positions))
        self._index = 0

    def next(self) -> tuple[str, int, str]:
        pos = self._positions[self._index]
        self._index = (self._index + 1) % len(self._positions)
        return pos


class RandomProgression:
    def __init__(self, positions: list[tuple[str, int, str]]):
        self._positions = positions
        self._last: tuple[str, int, str] | None = None

    def next(self) -> tuple[str, int, str]:
        if len(self._positions) == 1:
            self._last = self._positions[0]
            return self._last
        candidates = [p for p in self._positions if p != self._last]
        self._last = random.choice(candidates)
        return self._last


class CustomProgression:
    def __init__(self, pattern: list[tuple[str, int, str]]):
        self._pattern = pattern
        self._index = 0

    def next(self) -> tuple[str, int, str]:
        pos = self._pattern[self._index]
        self._index = (self._index + 1) % len(self._pattern)
        return pos
