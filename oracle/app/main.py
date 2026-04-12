# oracle/app/main.py
"""
FastAPI application - REST API for MSME Finance Platform
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.database import get_db
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MSME Finance Oracle API",
    description="Blockchain-based financing platform for MSMEs using government orders",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# HEALTH CHECK & STATUS
# ============================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "MSME Finance Oracle API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Test blockchain connection
    try:
        from services.blockchain_client import get_blockchain_client
        client = get_blockchain_client(use_mock=True)
        blockchain_status = "healthy" if client.is_connected() else "unhealthy"
    except Exception as e:
        logger.error(f"Blockchain health check failed: {e}")
        blockchain_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" and blockchain_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "blockchain": blockchain_status
        }
    }


@app.get("/status")
async def system_status(db: Session = Depends(get_db)):
    """Detailed system status"""
    from app.models import GeMOrder, MSME, User
    
    try:
        # Get statistics
        total_orders = db.query(GeMOrder).count()
        active_orders = db.query(GeMOrder).filter(
            GeMOrder.status.in_(['DETECTED', 'CONTRACT_CREATED', 'FUNDED', 'PRODUCTION'])
        ).count()
        completed_orders = db.query(GeMOrder).filter_by(status='REPAID').count()
        total_msmes = db.query(MSME).count()
        total_users = db.query(User).count()
        
        return {
            "platform": {
                "total_orders": total_orders,
                "active_orders": active_orders,
                "completed_orders": completed_orders,
                "total_msmes": total_msmes,
                "total_users": total_users
            },
            "oracle": {
                "environment": settings.ENVIRONMENT,
                "gem_monitoring": "active",
                "gstn_verification": "active"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        # Return default values instead of raising exception
        return {
            "platform": {
                "total_orders": 0,
                "active_orders": 0,
                "completed_orders": 0,
                "total_msmes": 0,
                "total_users": 0
            },
            "oracle": {
                "environment": settings.ENVIRONMENT,
                "gem_monitoring": "active",
                "gstn_verification": "active"
            },
            "error": str(e)
        }
# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================
# INCLUDE ROUTERS
# ============================================

# Import and include route modules
try:
    from app.api.routes import orders, msme, investors, admin
    
    app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
    app.include_router(msme.router, prefix="/api/msme", tags=["MSME"])
    app.include_router(investors.router, prefix="/api/investors", tags=["Investors"])
    app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
    
    logger.info("All API routes loaded successfully")
except Exception as e:
    logger.warning(f"Could not load all routes: {e}")
    logger.info("API will start with basic endpoints only")


# ============================================
# STARTUP & SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting MSME Finance Oracle API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Test database connection
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down MSME Finance Oracle API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )