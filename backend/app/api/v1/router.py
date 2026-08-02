from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth, users, courses, assignments, rubrics, submissions, instructor, reports, health
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["System Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(rubrics.router, prefix="/rubrics", tags=["Rubrics"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
api_router.include_router(instructor.router, prefix="/instructor", tags=["Instructor Operations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Analytics"])
