import random
import time
from typing import Callable, Iterable, Tuple
import socket

try:
    from googleapiclient.errors import HttpError  # type: ignore
except Exception:  # pragma: no cover
    HttpError = None  # type: ignore


def exponential_backoff_retry(
    func: Callable,
    args: Tuple = (),
    kwargs: dict = None,
    is_retryable: Callable[[Exception], bool] = lambda e: True,
    base_seconds: float = 1.0,
    factor: float = 2.0,
    max_seconds: float = 60.0,
    max_retries: int = 6,
):
    kwargs = kwargs or {}
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            attempt += 1
            if attempt > max_retries or not is_retryable(exc):
                raise
            sleep = min(max_seconds, base_seconds * (factor ** (attempt - 1)))
            sleep = sleep * (0.5 + random.random())  # jitter 0.5x-1.5x
            time.sleep(sleep)


def is_retryable_googleapi_error(exc: Exception) -> bool:
    # Network/timeouts
    if isinstance(exc, (socket.timeout, TimeoutError, ConnectionError)):
        return True
    # HTTP 429/5xx from googleapiclient
    if HttpError is not None and isinstance(exc, HttpError):
        try:
            status = int(getattr(exc, "status_code", 0) or exc.resp.status)
        except Exception:
            status = 0
        return status in (429, 500, 502, 503, 504)
    return False

