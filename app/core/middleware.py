import logging
import time

from fastapi import Request

log = logging.getLogger("app.request")


async def log_requests(request: Request, call_next):
    """One log line per request: 'GET /health 200 1.2ms' (shows up in Render Logs)."""
    start = time.perf_counter()
    status = 500  # if the handler raises, it is a 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        ms = (time.perf_counter() - start) * 1000
        log.info("%s %s %d %.1fms", request.method, request.url.path, status, ms)
