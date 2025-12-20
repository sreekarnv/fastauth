from fastauth.security.rate_limit import RateLimiter

login_rate_limiter = RateLimiter(
    max_attempts=5,
    window_seconds=60,
)

register_rate_limiter = RateLimiter(
    max_attempts=3,
    window_seconds=60,
)
