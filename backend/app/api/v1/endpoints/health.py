from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.api.deps import get_db
from backend.app.core.storage import storage_manager

router = APIRouter()


@router.get("/")
def get_system_health(db: Session = Depends(get_db)):
    # 1. Test Database Connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    # 2. Test Storage Writable
    try:
        sub_dir = storage_manager.get_submission_dir(1, 1, 1)
        storage_status = "writable" if sub_dir.exists() else "created"
    except Exception as e:
        storage_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "system": "AI-Powered Automated Code Reviewer & Feedback System",
        "version": "1.0.0",
        "database": db_status,
        "storage": storage_status,
        "supported_languages": ["python", "javascript", "java", "c", "cpp", "csharp"],
    }
