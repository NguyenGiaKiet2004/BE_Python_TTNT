import logging
import cv2
import numpy as np
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from app.models.face_model import face_model_instance, FaceModel
from app.schemas.response import VerifyResponse

router = APIRouter()

# Giới hạn dung lượng và kích thước ảnh
MAX_FILE_SIZE_MB = 5
MAX_DIMENSION = 640

def get_face_model() -> FaceModel:
    """Dependency injection for the FaceModel instance."""
    return face_model_instance

@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Verify a Face against a specific user ID"
)
async def verify_face_endpoint(
    face_image: UploadFile = File(..., description="An image file to verify."),
    user_id_to_verify: int = Form(..., description="The user ID to compare against."),
    model: FaceModel = Depends(get_face_model)
):
    """
    Receives an image and a specific user_id, and verifies if they are a match.
    This is a 1-to-1 comparison.
    """
    if face_image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

    try:
        # 1. Đọc toàn bộ file
        image_bytes = await face_image.read()

        # 2. Kiểm tra dung lượng file
        size_in_mb = len(image_bytes) / (1024 * 1024)
        if size_in_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail=f"Image too large ({size_in_mb:.2f} MB). Max allowed is {MAX_FILE_SIZE_MB} MB.")

        # 3. Decode bằng OpenCV
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Unable to decode image. Ensure it's a valid JPG or PNG.")

        # 4. Resize nếu ảnh quá lớn
        h, w = img.shape[:2]
        if max(h, w) > MAX_DIMENSION:
            scale = MAX_DIMENSION / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h))

        # 5. Encode lại về bytes để đưa vào model
        success, buffer = cv2.imencode(".jpg", img)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to re-encode image after resizing.")
        processed_bytes = buffer.tobytes()

        # 6. Gọi model để verify
        is_verified = model.verify_face(
            image_bytes=processed_bytes,
            user_id_to_verify=user_id_to_verify
        )

        return VerifyResponse(verified=is_verified)

    except ValueError as e:
        logging.warning(f"Verification validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred during verification: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")


# import logging
# from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
# from app.models.face_model import face_model_instance, FaceModel
# from app.schemas.response import VerifyResponse

# router = APIRouter()

# def get_face_model() -> FaceModel:
#     """Dependency injection for the FaceModel instance."""
#     return face_model_instance

# @router.post(
#     "/verify",
#     response_model=VerifyResponse,
#     summary="Verify a Face against a specific user ID"
# )
# async def verify_face_endpoint(
#     face_image: UploadFile = File(..., description="An image file to verify."),
#     user_id_to_verify: int = Form(..., description="The user ID to compare against."),
#     model: FaceModel = Depends(get_face_model)
# ):
#     """
#     Receives an image and a specific user_id, and verifies if they are a match.
#     This is a 1-to-1 comparison.
#     """
#     if face_image.content_type not in ["image/jpeg", "image/png"]:
#         raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

#     try:
#         image_bytes = await face_image.read()
#         is_verified = model.verify_face(
#             image_bytes=image_bytes,
#             user_id_to_verify=user_id_to_verify
#         )
#         return VerifyResponse(verified=is_verified)
#     except ValueError as e:
#         logging.warning(f"Verification validation error: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logging.error(f"An unexpected error occurred during verification: {e}")
#         raise HTTPException(status_code=500, detail="An internal server error occurred.")