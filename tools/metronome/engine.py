import time
import threading


class MetronomeEngine:
    def __init__(self, state, on_tick):
        self.state = state
        self.on_tick = on_tick
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def join(self) -> None:
        if self._thread:
            self._thread.join()

    def _loop(self) -> None:
        last_bpm = self.state.bpm
        interval = 60.0 / last_bpm
        next_tick = time.perf_counter() + interval

        while self.state.running:
            bpm = self.state.bpm
            if bpm != last_bpm:
                last_bpm = bpm
                interval = 60.0 / bpm
                # Reset schedule so BPM change takes effect immediately next beat
                next_tick = time.perf_counter() + interval

            # Coarse sleep to keep CPU usage low
            remaining = next_tick - time.perf_counter()
            if remaining > 0.01:
                time.sleep(remaining - 0.008)

            # Fine busy-wait for sub-millisecond precision
            while time.perf_counter() < next_tick:
                if not self.state.running:
                    return

            if self.state.running:
                self.on_tick()

            next_tick += interval
