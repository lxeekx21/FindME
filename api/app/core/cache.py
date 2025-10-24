import time
import threading
from functools import wraps
from typing import Any, Callable, Dict, Tuple


class TTLCache:
    def __init__(self):
        self._data: Dict[Any, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: Any) -> Any | None:
        with self._lock:
            if key in self._data:
                expires_at, value = self._data[key]
                if expires_at >= time.time():
                    return value
                else:
                    del self._data[key]
            return None

    def set(self, key: Any, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._data[key] = (time.time() + ttl_seconds, value)

    def clear(self):
        with self._lock:
            self._data.clear()


_global_cache = TTLCache()


def ttl_cache(ttl_seconds: int = 60):
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = (func.__module__, func.__qualname__, args, tuple(sorted(kwargs.items())))
            cached = _global_cache.get(key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            _global_cache.set(key, result, ttl_seconds)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = (func.__module__, func.__qualname__, args, tuple(sorted(kwargs.items())))
            cached = _global_cache.get(key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            _global_cache.set(key, result, ttl_seconds)
            return result

        if hasattr(func, "__call__") and func.__code__.co_flags & 0x80:
            return async_wrapper
        return sync_wrapper

    return decorator
