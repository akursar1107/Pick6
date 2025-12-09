"""FastAPI application entry point"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.api import api_router
from app.worker.scheduler import get_scheduler, configure_jobs

# Initialize logging
setup_logging(log_level="INFO" if not settings.DEBUG else "DEBUG")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.

    Requirements: 7.1, 7.2, 7.3
    """
    # Startup
    logger.info("Starting First6 API application")

    # Initialize and start scheduler
    scheduler = get_scheduler()
    configure_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started successfully")

    yield

    # Shutdown
    logger.info("Shutting down First6 API application")

    # Shutdown scheduler
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down successfully")


app = FastAPI(
    title="First6 API",
    description="NFL Prediction Tracking Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "admin-import",
            "description": "Admin endpoints for importing NFL season data from nflreadpy. "
            "**Authentication Required:** All endpoints require admin user authentication. "
            "Use these endpoints to import game schedules, scores, and touchdown scorer data.",
        },
        {
            "name": "auth",
            "description": "Authentication and user management endpoints",
        },
        {
            "name": "games",
            "description": "Game data and schedule endpoints",
        },
        {
            "name": "picks",
            "description": "User pick management endpoints",
        },
        {
            "name": "leaderboard",
            "description": "Scoring and leaderboard endpoints",
        },
        {
            "name": "health",
            "description": "Health check and system status endpoints",
        },
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "First6 API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy"}
