from fastapi import FastAPI
from app.middleware.logging_middleware import LoggingMiddleware
from app.config import configure_logging
from app.endpoints.auth import router as auth_router
from app.core.init_db import init_db
import structlog
import os

app = FastAPI(
    title="Simple Auth API",
    description="A simple authentication API with FastAPI",
    version="1.0.0"
)

app.add_middleware(LoggingMiddleware)

configure_logging(
    log_level=os.getenv("LOG_LEVEL", "DEBUG"),
    json_logs=os.getenv("JSON_LOGS", "true").lower() == "false"
)

logger = structlog.get_logger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization completed")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
