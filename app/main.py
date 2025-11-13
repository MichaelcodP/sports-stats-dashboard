from fastapi import FastAPI, Request
from app.routes import analysis, matches
from app.routes.health import router as health_router
import logging as _logging
import os
import time


def setup_logging():
    root = _logging.getLogger()
    level = os.getenv("LOG_LEVEL", "INFO")
    root.setLevel(level)
    handler = _logging.StreamHandler()
    try:
        from pythonjsonlogger import jsonlogger

        fmt = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    except ImportError:
        fmt = _logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    root.handlers = [handler]


setup_logging()
logger = _logging.getLogger("sports-stats-app")

app = FastAPI(title="Sports Stats API 🏆")

app.include_router(matches.router, prefix="/api", tags=["Matches"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(health_router, prefix="/api", tags=["Health"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.info(
        "request.start", extra={"path": request.url.path, "method": request.method}
    )
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request.error", extra={"path": request.url.path, "method": request.method}
        )
        raise
    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        "request.end",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.get("/")
def root():
    return {"message": "Sports Stats API is running 🏆"}
