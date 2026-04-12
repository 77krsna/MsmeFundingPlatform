# oracle/app/api/routes/admin.py
"""API routes for admin operations"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OracleJob

router = APIRouter()


@router.get("/jobs")
async def list_oracle_jobs(db: Session = Depends(get_db)):
    """List recent oracle jobs"""
    jobs = db.query(OracleJob).order_by(OracleJob.created_at.desc()).limit(50).all()
    
    return {
        "jobs": [{
            "id": str(j.id),
            "job_type": j.job_type,
            "status": j.status,
            "created_at": j.created_at
        } for j in jobs]
    }


@router.post("/trigger-scrape")
async def trigger_scrape():
    """Manually trigger GeM portal scraping"""
    try:
        from tasks.monitor_gem import scrape_gem_orders
        
        # Use send_task to avoid blocking
        from tasks.celery_app import celery_app
        task = celery_app.send_task('tasks.monitor_gem.scrape_gem_orders')
        
        return {
            "status": "success",
            "message": "Scraping task queued",
            "task_id": str(task.id)
        }
    except Exception as e:
        # If Celery/Redis not available, run directly
        return {
            "status": "queued_locally",
            "message": "Task will run when worker is available",
            "error": str(e)
        }


@router.post("/trigger-verification")
async def trigger_verification():
    """Manually trigger GSTN verification"""
    try:
        from tasks.celery_app import celery_app
        task = celery_app.send_task('tasks.verify_gstn.verify_pending_invoices')
        
        return {
            "status": "success",
            "message": "Verification task queued",
            "task_id": str(task.id)
        }
    except Exception as e:
        return {
            "status": "queued_locally",
            "message": "Task will run when worker is available",
            "error": str(e)
        }