import time
import threading


class ChordScheduler:
    def __init__(self, state, on_tick):
        self.state = state
        self.on_tick = on_tick
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        interval = self.state.interval
        next_tick = time.perf_counter() + interval
        self.state.next_tick_at = next_tick

        while self.state.running:
            if self.state.paused:
                time.sleep(0.02)
                next_tick = time.perf_counter() + interval
                self.state.next_tick_at = next_tick
                continue

            if self.state.skip_requested:
                self.state.skip_requested = False
                if self.state.running:
                    self.on_tick()
                next_tick = time.perf_counter() + interval
                self.state.next_tick_at = next_tick
                continue

            now = time.perf_counter()
            if now >= next_tick:
                if self.state.running:
                    self.on_tick()
                next_tick += interval
                self.state.next_tick_at = next_tick
                continue

            remaining = next_tick - now
            time.sleep(min(remaining * 0.5, 0.05))
