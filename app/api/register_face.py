import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from app.models.face_model import face_model_instance, FaceModel
from app.schemas.response import FaceRegisterResponse

router = APIRouter()

def get_face_model() -> FaceModel:
    """Dependency injection for the FaceModel instance."""
    return face_model_instance

@router.post(
    "/register",
    response_model=FaceRegisterResponse,
    summary="Register a New Face for a specific user"
)
async def register_face_endpoint(
    user_id: int = Form(..., description="The ID of the user to register the face for."),
    file: UploadFile = File(..., description="An image file (JPG or PNG) containing one face."),
    model: FaceModel = Depends(get_face_model)
):
    """
    Receives an image and a user_id, processes the image to extract facial data,
    and stores it in the database.
    """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:
        image_bytes = await file.read()
        model.register_new_face(user_id=user_id, image_bytes=image_bytes)
        return FaceRegisterResponse(user_id=user_id)
    except ValueError as e:
        logging.warning(f"Registration validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred during registration: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")