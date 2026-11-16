import time
from collections import defaultdict
from threading import Lock
from flask import request, jsonify
from functools import wraps

class InMemoryRateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        with self.lock:
            # Clean up old requests outside the sliding window
            timestamps = [t for t in self.requests[key] if now - t < window_seconds]
            if len(timestamps) >= max_requests:
                self.requests[key] = timestamps
                return True
            timestamps.append(now)
            self.requests[key] = timestamps
            return False

limiter = InMemoryRateLimiter()

def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    Decorator to rate-limit endpoints per client IP.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
            key = f"{ip}:{request.endpoint}"
            if limiter.is_rate_limited(key, max_requests, window_seconds):
                return jsonify({
                    "success": False,
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please wait a moment before trying again."
                }), 429
            return f(*args, **kwargs)
        return decorated
    return decorator
