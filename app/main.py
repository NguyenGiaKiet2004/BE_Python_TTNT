import logging
from fastapi import FastAPI

from .api import register_face, health, recognize, verify, auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Face Recognition API",
    description="A modular microservice for face recognition with auth support.",
    version="2.0.0"
)

# Giữ prefix "/api/v1" ở main
app.include_router(health.router, prefix="/api/v1", tags=["Monitoring"])
app.include_router(register_face.router, prefix="/api/v1", tags=["Registration"])
app.include_router(recognize.router, prefix="/api/v1", tags=["Recognition"])
app.include_router(verify.router, prefix="/api/v1", tags=["Verification"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
