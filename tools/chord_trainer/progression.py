import random


class LinearProgression:
    _ORDER = ["A", "E", "D", "C", "G"]

    def __init__(self, chords: list[str]):
        self._sequence = [c for c in self._ORDER if c in chords]
        self._index = 0

    def next(self) -> str:
        chord = self._sequence[self._index]
        self._index = (self._index + 1) % len(self._sequence)
        return chord


class RandomProgression:
    def __init__(self, chords: list[str]):
        self._chords = chords
        self._last: str | None = None

    def next(self) -> str:
        if len(self._chords) == 1:
            self._last = self._chords[0]
            return self._last
        candidates = [c for c in self._chords if c != self._last]
        self._last = random.choice(candidates)
        return self._last


class CustomProgression:
    def __init__(self, pattern: list[str]):
        self._pattern = pattern
        self._index = 0

    def next(self) -> str:
        chord = self._pattern[self._index]
        self._index = (self._index + 1) % len(self._pattern)
        return chord
