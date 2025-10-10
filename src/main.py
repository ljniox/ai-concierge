"""
WhatsApp AI Concierge Service
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
import asyncio

from src.api.health import health_router
from src.api.webhook import webhook_router
from src.api.orchestrate import orchestrate_router
from src.api.sessions import sessions_router
from src.api.admin import admin_router
from src.api.temporary_pages import router as temporary_pages_router
from src.api.file_management import router as file_management_router
from src.api.telegram import telegram_router
from src.services.interaction_service import InteractionService
from src.services.cleanup_service import start_cleanup_service, stop_cleanup_service

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Initialize services on startup
    interaction_service = InteractionService()
    await interaction_service.initialize_redis()

    # Start cleanup service in background
    cleanup_task = asyncio.create_task(start_cleanup_service())

    logger.info("services_initialized")

    yield

    # Cleanup on shutdown
    await stop_cleanup_service()
    logger.info("application_shutdown")

app = FastAPI(
    title="WhatsApp AI Concierge API",
    description="Multi-service WhatsApp concierge with AI orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "incoming_request",
        method=request.method,
        url=str(request.url),
        headers=dict(request.headers)
    )

    response = await call_next(request)

    logger.info(
        "outgoing_response",
        status_code=response.status_code,
        headers=dict(response.headers)
    )

    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )

# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["system"])
app.include_router(webhook_router, prefix="/api/v1", tags=["webhook"])
app.include_router(orchestrate_router, prefix="/api/v1", tags=["orchestration"])
app.include_router(sessions_router, prefix="/api/v1", tags=["sessions"])
app.include_router(admin_router, prefix="/api/v1", tags=["admin"])
app.include_router(telegram_router, prefix="/api/v1", tags=["telegram"])
app.include_router(temporary_pages_router, tags=["temporary-pages"])

# Include temporary pages view endpoints without API prefix
from src.api.temporary_pages import view_router
app.include_router(view_router)
app.include_router(file_management_router, prefix="/api/v1/files", tags=["file-management"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "WhatsApp AI Concierge Service", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )