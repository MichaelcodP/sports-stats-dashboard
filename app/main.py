import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
    logger.info("Starting background tasks...")
    # Delay to avoid rate limits on startup
    await asyncio.sleep(5)
    asyncio.create_task(fetch_and_store_matches())
    yield
    logger.info("Application shutdown complete.")


# ----------------- FastAPI App -----------------
app = FastAPI(title="Sports Stats API 🏆", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

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
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
