"""Pembatas laju sederhana di memori proses (backend berjalan sebagai satu proses uvicorn)."""
import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Izinkan paling banyak `limit` kejadian per `window` detik untuk setiap kunci."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self._events: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        events = self._events[key]
        while events and now - events[0] >= self.window:
            events.popleft()
        if not events:
            del self._events[key]
            return deque()
        return events

    def retry_after(self, key: str) -> int:
        """Detik sampai kunci boleh dipakai lagi; 0 jika belum mencapai batas."""
        with self._lock:
            now = time.monotonic()
            events = self._prune(key, now)
            if len(events) < self.limit:
                return 0
            return max(1, int(self.window - (now - events[0])) + 1)

    def hit(self, key: str) -> None:
        with self._lock:
            self._events[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)
