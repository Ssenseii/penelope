import time
import keyboard

from config.constants import MIN_BPM, MAX_BPM, TAP_TEMPO_SAMPLE_SIZE


class InputHandler:
    def __init__(self, state):
        self.state = state
        self._hooks: list = []

    def start(self) -> None:
        self._hooks = [
            keyboard.on_press_key("up",    self._on_up,         suppress=True),
            keyboard.on_press_key("down",  self._on_down,       suppress=True),
            keyboard.on_press_key("a",     self._on_accent,     suppress=True),
            keyboard.on_press_key("t",     self._on_tap_toggle, suppress=True),
            keyboard.on_press_key("space", self._on_tap_space,  suppress=True),
            keyboard.on_press_key("q",     self._on_quit,       suppress=True),
        ]

    def stop(self) -> None:
        for hook in self._hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._hooks.clear()

    def _on_up(self, _e) -> None:
        self.state.bpm = min(self.state.bpm + 1, MAX_BPM)

    def _on_down(self, _e) -> None:
        self.state.bpm = max(self.state.bpm - 1, MIN_BPM)

    def _on_accent(self, _e) -> None:
        self.state.accent_enabled = not self.state.accent_enabled

    def _on_tap_toggle(self, _e) -> None:
        self.state.tap_mode = not self.state.tap_mode
        if not self.state.tap_mode:
            self.state.tap_times.clear()

    def _on_tap_space(self, _e) -> None:
        if not self.state.tap_mode:
            return
        now = time.perf_counter()
        self.state.tap_times.append(now)
        # Keep only the window needed for the rolling average
        if len(self.state.tap_times) > TAP_TEMPO_SAMPLE_SIZE + 1:
            self.state.tap_times = self.state.tap_times[-(TAP_TEMPO_SAMPLE_SIZE + 1):]
        if len(self.state.tap_times) >= 2:
            intervals = [
                self.state.tap_times[i] - self.state.tap_times[i - 1]
                for i in range(1, len(self.state.tap_times))
            ]
            avg = sum(intervals) / len(intervals)
            new_bpm = round(60.0 / avg)
            self.state.bpm = max(MIN_BPM, min(MAX_BPM, new_bpm))

    def _on_quit(self, _e) -> None:
        self.state.running = False
