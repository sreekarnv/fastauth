import pytest
from fastauth.security.rate_limit import RateLimiter, RateLimitExceeded


def test_rate_limiter_blocks_after_max_attempts():
    limiter = RateLimiter(max_attempts=3, window_seconds=60)
    key = "test-key"

    limiter.hit(key)
    limiter.hit(key)
    limiter.hit(key)

    with pytest.raises(RateLimitExceeded):
        limiter.hit(key)


def test_rate_limiter_resets():
    limiter = RateLimiter(max_attempts=1, window_seconds=60)
    key = "test-key"

    limiter.hit(key)
    limiter.reset(key)

    limiter.hit(key)
