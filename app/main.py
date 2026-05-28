from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth, cites, locataires, annonces, notifications
from app.utils.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Démarrage Mon Compagnon API...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables vérifiées")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("👋 Arrêt API")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API de gestion de cités universitaires — Mon Compagnon",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée : {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Erreur interne", "detail": str(exc)},
    )


PREFIX = "/api/v1"
app.include_router(auth.router,          prefix=PREFIX)
app.include_router(cites.router,         prefix=PREFIX)
app.include_router(locataires.router,    prefix=PREFIX)
app.include_router(annonces.router,      prefix=PREFIX)
app.include_router(notifications.router, prefix=PREFIX)


@app.get("/", tags=["Santé"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Santé"])
def health():
    return {"status": "ok"}
