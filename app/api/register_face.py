import logging
from typing import Optional, Tuple
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, status   
from app.models.face_model import face_model_instance, FaceModel
from app.schemas.response import FaceRegisterSuccessResponse

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import sql_models
from app.core.database import SessionLocal

router = APIRouter()

def get_face_model() -> FaceModel:
    """Dependency injection for the FaceModel instance."""
    return face_model_instance

@router.post(
    "/register-face",
    response_model=FaceRegisterSuccessResponse,
    summary="Register a New Face for a specific user",
    status_code=status.HTTP_201_CREATED 
)
async def register_face_endpoint(
    user_id: int = Form(..., description="The ID of the user to register the face for."),
    image: UploadFile = File(..., description="An image file (JPG or PNG) containing one face."),
    model: FaceModel = Depends(get_face_model)
):
    """
    Receives an image and a user_id, processes the image to extract facial data,
    and stores it in the database.
    """
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:


        image_bytes = await image.read()
        # existing_face : Tuple[bool, Optional[uuid.UUID]] = model.recognize_face(image_bytes=image_bytes)

        # db: Session = SessionLocal()
        # existing_face_data = db.scalars(
        #     select(sql_models.FacialData).where(sql_models.FacialData.user_id == user_id and sql_models.FacialData.encoding_face_UUID == existing_face[1].bytes)
        # ).first()
        # if not (existing_face[0] and existing_face_data and existing_face == existing_face_data):
        #     raise HTTPException(status_code=409, detail="Face already registered for this user.")
        # else:
        #     encoding_UUID = model.register_new_face(image_bytes=image_bytes)
        #     db.add(sql_models.FacialData(user_id=user_id, encoding_UUID = encoding_UUID.bytes)) #note that will store uuid as binary(16), so .bytes will convert uuid from varchar(36) to binary(16)
        #     db.commit()      
        #     return FaceRegisterSuccessResponse(user_id=user_id)
        existing_face : Tuple[bool, Optional[uuid.UUID]] = model.recognize_face(image_bytes=image_bytes)
        if existing_face[0]:
            db: Session = SessionLocal()
            existing_face_data = db.scalars(
            select(sql_models.FacialData).where(sql_models.FacialData.user_id == user_id & sql_models.FacialData.encoding_face_UUID == existing_face[1].bytes)).first()
            if existing_face_data:
                raise HTTPException(status_code=409, detail="Face already registered for this user.")
        else:
            encoding_UUID = model.register_new_face(image_bytes=image_bytes)
            db: Session = SessionLocal()
            db.add(sql_models.FacialData(user_id=user_id, encoding_UUID = encoding_UUID.bytes)) #note that will store uuid as binary(16), so .bytes will convert uuid from varchar(36) to binary(16)
            db.commit()      
            return FaceRegisterSuccessResponse(user_id=user_id)


    
    except ValueError as e:
        logging.warning(f"Registration validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred during registration: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
            db.close()