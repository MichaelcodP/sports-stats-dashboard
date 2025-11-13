import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.routes import analysis, matches, metrics
from app.routes.health import router as health_router
from app.services.data_updater import fetch_and_store_matches


# ----------------- Logging Setup -----------------
def setup_logging():
    root = logging.getLogger()
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root.setLevel(level)
    handler = logging.StreamHandler()
    try:
        from pythonjsonlogger import jsonlogger

        fmt = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    except ImportError:
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    root.handlers = [handler]


setup_logging()
logger = logging.getLogger("sports-stats-app")


# ----------------- Lifespan Handler -----------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, що виконується при старті сервера
    logger.info("Starting background tasks...")
    asyncio.create_task(fetch_and_store_matches())
    yield
    # Код, що виконується при завершенні сервера (закриття ресурсів можна додати тут)
    logger.info("Application shutdown complete.")


# ----------------- FastAPI App -----------------
app = FastAPI(title="Sports Stats API 🏆", lifespan=lifespan)

# ----------------- Routers -----------------
app.include_router(matches.router, prefix="/api", tags=["Matches"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(health_router, prefix="/api", tags=["Health"])


# ----------------- Middleware -----------------
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


# ----------------- Root Endpoint -----------------
@app.get("/")
def root():
    return {"message": "Sports Stats API is running 🏆"}
