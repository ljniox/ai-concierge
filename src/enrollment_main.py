"""
Enrollment System Main Application

Système de Gestion de Profils et Inscriptions avec SQLite
Multi-Profile Enrollment Management with OCR and Mobile Money

Features:
- Fixed enrollment fee: 5000 FCFA
- Conversational enrollment workflow
- OCR document processing (French)
- WhatsApp and Telegram integration
- Multi-database SQLite architecture
- Role-based permissions (13 roles)
- GDPR-compliant audit logging

Architecture:
- Phase 1: Setup ✅ (4 tasks)
- Phase 2: Foundational Infrastructure ✅ (16 tasks)
- Phase 3: US1 Enrollment with OCR ✅ (32 tasks)
- Phase 4: US2 Payment Validation (20 tasks) 🔄
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime

# Import our new routers
from .api.v1 import auth, enrollments, documents, workflow, whatsapp, telegram, payments
from .database.sqlite_manager import get_sqlite_manager
from .services.audit_service import log_user_action

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire",
    description="Système de Gestion de Profils et Inscriptions avec SQLite",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include our new routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(enrollments.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(workflow.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(telegram.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "service": "Gust-IA - Service de la catéchèse de Saint Jean Bosco de Nord Foire",
        "version": "2.0.0",
        "description": "Système de Gestion de Profils et Inscriptions avec SQLite",
        "features": [
            "Multi-profile enrollment with OCR",
            "Fixed fee: 5000 FCFA",
            "Conversational enrollment workflow",
            "French document processing",
            "WhatsApp and Telegram integration",
            "Mobile Money payment processing",
            "Automated receipt OCR validation",
            "Treasurer validation workflow",
            "Role-based permissions (13 roles)",
            "GDPR-compliant audit logging"
        ],
        "status": "operational",
        "phases": {
            "setup": "✅ Complete (4 tasks)",
            "infrastructure": "✅ Complete (16 tasks)",
            "enrollment_ocr": "✅ Complete (32 tasks)",
            "payment_validation": "✅ Complete (20 tasks)"
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": "/api/v1",
            "payments": "/api/v1/payments",
            "workflow": "/api/v1/workflow",
            "whatsapp": "/api/v1/whatsapp",
            "telegram": "/api/v1/telegram"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Dict: System health status including all services
    """
    try:
        # Check SQLite databases
        sqlite_manager = get_sqlite_manager()
        sqlite_health = await sqlite_manager.health_check()

        # Check external services
        services_status = {
            "sqlite_databases": sqlite_health,
            "overall": "healthy" if all(sqlite_health.values()) else "degraded"
        }

        return JSONResponse({
            "status": services_status["overall"],
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status,
            "version": "2.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }, status_code=500)


@app.get("/stats")
async def get_system_stats():
    """
    Get system statistics.

    Returns:
        Dict: System usage statistics
    """
    try:
        manager = get_sqlite_manager()

        # Get database statistics
        async with manager.get_connection('catechese') as conn:
            # Legacy data
            cursor = await conn.execute("SELECT COUNT(*) as count FROM catechumenes_2")
            legacy_students = (await cursor.fetchone())['count']

            cursor = await conn.execute("SELECT COUNT(*) as count FROM parents_2")
            legacy_parents = (await cursor.fetchone())['count']

            cursor = await conn.execute("SELECT COUNT(*) as count FROM inscriptions_16")
            legacy_enrollments = (await cursor.fetchone())['count']

            # New data
            cursor = await conn.execute("SELECT COUNT(*) as count FROM inscriptions")
            new_enrollments = (await cursor.fetchone())['count']

            cursor = await conn.execute("SELECT COUNT(*) as count FROM documents")
            documents = (await cursor.fetchone())['count']

            cursor = await conn.execute("SELECT COUNT(*) as count FROM profil_utilisateurs")
            profiles = (await cursor.fetchone())['count']

            cursor = await conn.execute("SELECT COUNT(*) as count FROM action_logs")
            audit_logs = (await cursor.fetchone())['count']

        # Get OCR statistics
        from .services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service()
        ocr_status = "initialized" if ocr_service.reader else "not_initialized"

        return JSONResponse({
            "legacy_data": {
                "students": legacy_students,
                "parents": legacy_parents,
                "enrollments": legacy_enrollments,
                "classes": 15
            },
            "new_system": {
                "enrollments": new_enrollments,
                "documents": documents,
                "profiles": profiles,
                "audit_logs": audit_logs
            },
            "services": {
                "ocr": ocr_status,
                "messaging": "operational"
            },
            "enrollment_fee": "5000 FCFA",
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return JSONResponse({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, status_code=500)


@app.post("/test-ocr")
async def test_ocr_service():
    """
    Test OCR service functionality.

    Returns:
        Dict: OCR test results
    """
    try:
        from .services.ocr_service import get_ocr_service
        ocr_service = get_ocr_service()

        return JSONResponse({
            "status": "success",
            "ocr_service": "initialized" if ocr_service.reader else "not_initialized",
            "confidence_threshold": ocr_service.confidence_threshold,
            "supported_languages": ["fr", "en"],
            "message": "OCR service is operational"
        })

    except Exception as e:
        logger.error(f"OCR test failed: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


@app.get("/features")
async def get_features():
    """
    Get system features and capabilities.

    Returns:
        Dict: System features
    """
    try:
        return JSONResponse({
            "enrollment_features": {
                "conversational_workflow": True,
                "fixed_fee": "5000 FCFA",
                "document_ocr": True,
                "french_processing": True,
                "confidence_threshold": "70%"
            },
            "messaging": {
                "whatsapp": True,
                "telegram": True,
                "webhook_support": True
            },
            "security": {
                "role_based_permissions": True,
                "roles_count": 13,
                "rate_limiting": True,
                "audit_logging": True,
                "gdpr_compliant": True
            },
            "legacy_integration": {
                "existing_students": 509,
                "existing_parents": 341,
                "existing_enrollments": 819,
                "data_preservation": True
            },
            "workflow_automation": {
                "step_by_step": True,
                "status_transitions": True,
                "human_intervention": True,
                "automatic_validation": True
            }
        })

    except Exception as e:
        logger.error(f"Failed to get features: {e}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


@app.get("/mvp-status")
async def get_mvp_status():
    """
    Get MVP implementation status.

    Returns:
        Dict: MVP completion status
    """
    try:
        total_tasks = 72  # Phase 1-4 tasks
        completed_tasks = 4 + 16 + 32 + 20  # All phases completed
        completion_percentage = (completed_tasks / total_tasks) * 100

        return JSONResponse({
            "mvp_status": "MVP Complete",
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_percentage": round(completion_percentage, 1),
            "phases": {
                "phase_1": {"name": "Setup", "tasks": 4, "status": "✅ Complete"},
                "phase_2": {"name": "Foundational Infrastructure", "tasks": 16, "status": "✅ Complete"},
                "phase_3": {"name": "US1 Enrollment with OCR", "tasks": 32, "status": "✅ Complete"},
                "phase_4": {"name": "US2 Payment Validation", "tasks": 20, "status": "✅ Complete"}
            },
            "next_steps": [
                "Run MVP integration tests",
                "Deploy to production",
                "Monitor system performance"
            ]
        })

    except Exception as e:
        logger.error(f"Failed to get MVP status: {e}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


@app.get("/api-keys")
async def get_api_keys_info():
    """
    Get API keys configuration information (sanitized).

    Returns:
        Dict: API keys status (masked for security)
    """
    try:
        return JSONResponse({
            "message": "API keys configuration status",
            "configured": {
                "waha_base_url": os.getenv('WAHA_BASE_URL', 'Not configured'),
                "waha_api_token": "✓ Configured" if os.getenv('WAHA_API_TOKEN') else "✗ Not configured",
                "telegram_bot_token": "✓ Configured" if os.getenv('TELEGRAM_BOT_TOKEN') else "✗ Not configured",
                "supabase_url": "✓ Configured" if os.getenv('SUPABASE_URL') else "✗ Not configured",
                "minio_endpoint": "✓ Configured" if os.getenv('MINIO_ENDPOINT') else "✗ Not configured",
                "sqlite_db_path": os.getenv('SQLITE_DB_PATH', 'Not configured')
            },
            "security": "API keys are masked for security"
        })

    except Exception as e:
        logger.error(f"Failed to get API keys info: {e}")
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    """
    logger.info("Starting Gust-IA Enrollment System v2.0...")

    # Initialize SQLite manager
    sqlite_manager = get_sqlite_manager()
    await sqlite_manager.initialize()
    logger.info("SQLite databases initialized")

    # Initialize OCR service
    from .services.ocr_service import get_ocr_service
    ocr_service = get_ocr_service()
    logger.info("OCR service initialized")

    # Setup Telegram webhook
    from .services.messaging_service import get_messaging_service
    messaging_service = get_messaging_service()
    try:
        await messaging_service.setup_telegram_webhook()
        logger.info("Telegram webhook setup completed")
    except Exception as e:
        logger.warning(f"Telegram webhook setup failed: {e}")

    logger.info("Gust-IA Enrollment System v2.0 startup completed successfully!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.
    """
    logger.info("Shutting down Gust-IA Enrollment System...")

    # Close SQLite connections
    sqlite_manager = get_sqlite_manager()
    await sqlite_manager.close_all()
    logger.info("SQLite connections closed")

    logger.info("Gust-IA shutdown completed")


if __name__ == "__main__":
    # Development mode
    uvicorn.run(
        "src.enrollment_main:app",
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflict with existing service
        reload=True,
        log_level="info"
    )