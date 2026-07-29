import time


class PoliteRateLimiter:
    def __init__(self, delay_seconds: float) -> None:
        if delay_seconds < 0:
            raise ValueError(
                "delay_seconds cannot be negative"
            )

        self.delay_seconds = delay_seconds
        self._last_request_started: float | None = None

    def wait(self) -> None:
        now = time.monotonic()

        if self._last_request_started is not None:
            elapsed = (
                now - self._last_request_started
            )

            remaining = (
                self.delay_seconds - elapsed
            )

            if remaining > 0:
                time.sleep(remaining)

        self._last_request_started = (
            time.monotonic()
        )