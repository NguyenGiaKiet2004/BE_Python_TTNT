import logging

from fastapi import FastAPI
from app.api import register_face, health, recognize, verify, auth, attendance, user # Thêm auth và attendance vào đâ
from app.models import schemas

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Face Recognition API",
    description="A modular microservice for face recognition.",
    version="2.0.0"
)
app.include_router(health.router, prefix="/api/v1", tags=["Monitoring"])
app.include_router(register_face.router, prefix="/api/v1", tags=["Registration"])
app.include_router(recognize.router, prefix="/api/v1", tags=["Recognition"])
app.include_router(verify.router, prefix="/api/v1", tags=["Verification"])


# New APIs
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(attendance.router, prefix="/api/v1", tags=["Attendance"])

app.include_router(user.router, prefix="/api/v1", tags=["User Profile"])