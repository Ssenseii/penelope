import time
import keyboard


class InputHandler:
    def __init__(self, state):
        self.state = state
        self._hooks: list = []

    def start(self) -> None:
        self._hooks = [
            keyboard.on_press_key("space", self._on_pause, suppress=True),
            keyboard.on_press_key("right", self._on_skip,  suppress=True),
            keyboard.on_press_key("q",     self._on_quit,  suppress=True),
        ]

    def stop(self) -> None:
        for hook in self._hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._hooks.clear()

    def _on_pause(self, _e) -> None:
        if not self.state.paused:
            self.state._pause_start = time.perf_counter()
        else:
            self.state.total_paused += time.perf_counter() - self.state._pause_start
        self.state.paused = not self.state.paused

    def _on_skip(self, _e) -> None:
        self.state.skip_requested = True

    def _on_quit(self, _e) -> None:
        self.state.running = False
