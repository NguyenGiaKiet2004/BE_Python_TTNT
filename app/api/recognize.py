import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.face_model import face_model_instance, FaceModel
from app.models.sql_models import User
from app.core.database import SessionLocal
from app.schemas.response import RecognitionResponse

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_face_model() -> FaceModel:
    """Dependency injection for the FaceModel instance."""
    return face_model_instance

@router.post(
    "/recognize",
    response_model=RecognitionResponse,
    summary="Recognize a Face"
)
async def recognize_face_endpoint(
    file: UploadFile = File(..., description="An image file to check against the database."),
    model: FaceModel = Depends(get_face_model),
    db: Session = Depends(get_db)
):
    """
    Receives an image, finds the best match in the database, and returns the result.
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:
        image_bytes = await file.read()
        is_match, user_id = model.recognize_face(image_bytes=image_bytes)
        
        if is_match and user_id:
            user = db.query(User).filter(User.user_id == user_id).first()
            if user:
                return RecognitionResponse(user_id=user_id, full_name=user.full_name, status="matched")
        
        return RecognitionResponse(user_id=None, full_name=None, status="not_matched")

    except ValueError as e:
        logging.warning(f"Recognition validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred during recognition: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")