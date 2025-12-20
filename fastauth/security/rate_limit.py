import time
from collections import defaultdict, deque


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    def __init__(
        self,
        *,
        max_attempts: int,
        window_seconds: int,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._store: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> None:
        """
        Register an attempt for a given key.
        Raises RateLimitExceeded if limit is exceeded.
        """
        now = time.time()
        window_start = now - self.window_seconds

        attempts = self._store[key]

        while attempts and attempts[0] < window_start:
            attempts.popleft()

        if len(attempts) >= self.max_attempts:
            raise RateLimitExceeded("Too many attempts")

        attempts.append(now)

    def reset(self, key: str) -> None:
        """
        Clear attempts after successful auth.
        """
        self._store.pop(key, None)
