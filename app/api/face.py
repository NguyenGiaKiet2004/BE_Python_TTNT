import logging
import time
from typing import Optional, Tuple
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, status   
from app.models.face_model import face_model, FaceModel
from app.schemas.response import FaceRegisterSuccessResponse, RecognitionResponse, VerifyResponse, DeleteFaceResponse    

from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.models import sql_models
from app.core.database import SessionLocal, get_db

router = APIRouter()

def get_face_model() -> FaceModel:
    """Dependency injection for the FaceModel instance."""
    return face_model


############
# REGISTER FACE
############

@router.post(
    "/register-face",
    response_model=FaceRegisterSuccessResponse,
    tags=["Face Registration"],
    summary="Register a New Face for a specific user",
    status_code=status.HTTP_201_CREATED 
)
async def register_face_endpoint(
    user_id: int = Form(..., description="The ID of the user to register the face for."),
    face_image: UploadFile = File(..., description="An image file (JPG or PNG) containing one face."),
    model: FaceModel = Depends(get_face_model),
    db: Session = Depends(get_db)
):
    """
    Receives an image and a user_id, processes the image to extract facial data,
    and stores it in the database.
    """
    if face_image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:
        image_bytes = await face_image.read()
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
            select(sql_models.FacialData).where(and_(sql_models.FacialData.user_id == user_id, sql_models.FacialData.encoding_face_UUID == existing_face[1]))).first()
            if existing_face_data:
                raise HTTPException(status_code=409, detail=f"Face already registered for this user ({user_id}).")
            else:
                raise HTTPException(status_code=409, detail=f"This person's facial data has already existed in database")

        else:
            register_face: tuple[bool, uuid.UUID, str] = model.register_new_face(image_bytes=image_bytes)
            if register_face[0]:
                db: Session = SessionLocal()
                db.add(sql_models.FacialData(user_id=user_id, encoding_UUID = register_face[1], reference_image_url=register_face[2])) #note that will store uuid as binary(16), so .bytes will convert uuid from varchar(36) to binary(16)
                db.commit()      
                return FaceRegisterSuccessResponse(user_id=user_id)
            else: raise HTTPException(status_code=400, detail=str(e))

    except ValueError as e:
        logging.warning(f"Registration validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred during registration: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


############
# VERIFY FACE
############

@router.post(
    "/verify",
    response_model=VerifyResponse,
    tags=["Face Verification"],
    summary="Verify a Face against a specific user ID",
    status_code=status.HTTP_200_OK
)
async def verify_face_endpoint(
    face_image: UploadFile = File(..., description="An image file to verify."),
    user_id_to_verify: int = Form(..., description="The user ID to compare against."),
    model: FaceModel = Depends(get_face_model),
    db: Session = Depends(get_db)
):
    """
    Receives an image and a specific user_id, and verifies if they are a match.
    This is a 1-to-1 comparison.
    """
    if face_image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:
        get_Face_Data_FromDB = db.scalar(select(sql_models.FacialData).where(sql_models.FacialData.user_id == user_id_to_verify))
        if not get_Face_Data_FromDB:
            raise HTTPException(status_code=404, detail=f"This user {user_id_to_verify} doesn't exist in Face Database")
        image_bytes = await face_image.read()
        UUID_Object_encoding_UUID : uuid = (get_Face_Data_FromDB.encoding_face_UUID)
        start_time = time.perf_counter()
        isFaceVerified = model.verify_face(image_bytes=image_bytes, face_id_to_verify=UUID_Object_encoding_UUID)
        end_time = time.perf_counter()
        total_time = end_time - start_time

        return VerifyResponse(verified=isFaceVerified)
    
    except ValueError as e:
        logging.warning(f"Face Identity validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    
@router.post(
    "/recognize",
    response_model=RecognitionResponse,
    tags=["Face Recognition"],
    summary="Recognize a Face",
    status_code=status.HTTP_200_OK
)
async def recognize_face_endpoint(
    face_image: UploadFile = File(..., description="An image file to check against the database."),
    model: FaceModel = Depends(get_face_model),
    db: Session = Depends(get_db)
):
    """
    Receives an image, finds the best match in the database, and returns the result.
    """
    if face_image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:
        image_bytes = await face_image.read()
        is_match, encoding_UUID = model.recognize_face(image_bytes=image_bytes)
   
        if is_match:
            
            user_id_from_faceDB = db.scalar(select(sql_models.FacialData.user_id).where(sql_models.FacialData.encoding_face_UUID == encoding_UUID))

            
            if user_id_from_faceDB:
                user_from_userDB = db.scalar(select(sql_models.User).where(sql_models.User.user_id == user_id_from_faceDB))
                return RecognitionResponse(user_id=user_from_userDB.user_id, full_name=user_from_userDB.full_name, status="matched")
        
        return RecognitionResponse(user_id=None, full_name=None, status="not_matched")

    except ValueError as e:
        logging.warning(f"Recognition validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred during recognition: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    
@router.delete(
    "/delete-face",
    response_model=DeleteFaceResponse,
    tags=["Face Deletation"],
    status_code=status.HTTP_200_OK
)
async def delete_face_endpoint(
    user_id_to_delete: int = Form(..., description="The ID of the user to delete the face for."),
    model: FaceModel = Depends(get_face_model),
    db: Session = Depends(get_db)
):
    '''

    '''
    try:
        try:
            user_face_to_delete = db.query(sql_models.FacialData).filter(sql_models.FacialData.user_id == user_id_to_delete).first()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        if not user_face_to_delete:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id_to_delete} not found in Face database")
        try:
            db.delete(user_face_to_delete)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        deleted_face = model.delete_face(user_face_to_delete.encoding_face_UUID) 
        if deleted_face:
            return DeleteFaceResponse(user_id=user_id_to_delete)
        else:  
            raise HTTPException(status_code=500, detail=f"Deletation of user with id: {user_id_to_delete} failed.")
    except Exception as e:
        logging.error(f"An unexpected error occurred during face deletion: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
        
    