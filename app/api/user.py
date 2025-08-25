from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from app.models import sql_models, schemas
from app.core.database import SessionLocal
from app.core import security
from app.core.security import get_current_user
from app.core.exceptions import RegistrationError

router = APIRouter(tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me", response_model=schemas.User)
def get_current_user_profile(current_user: schemas.User = Depends(get_current_user)):
    return current_user

# @router.post("/register-face/{user_id}", response_model=schemas.FaceRegisterResponse)
# async def register_face(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
#     # Đây chỉ là logic giả định, bạn cần thay thế bằng mô hình xử lý khuôn mặt thực tế
#     try:
#         # Kiểm tra file type
#         if file.content_type not in ["image/jpeg", "image/png"]:
#             raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

#         # Đọc dữ liệu ảnh
#         image_bytes = await file.read()
        
#         # Xử lý ảnh để trích xuất encoding_data (logic thực tế)
#         # encoding_data = process_image_and_get_encoding(image_bytes)
#         encoding_data = b"sample_encoding_data" # Dữ liệu giả định

#         # Lưu vào database
#         new_face = sql_models.FacialData(
#             user_id=user_id,
#             encoding_data=encoding_data,
#             reference_image_url=f"http://example.com/images/{user_id}.jpg" # Lưu URL ảnh
#         )
#         db.add(new_face)
#         db.commit()
#         db.refresh(new_face)

#         return {"user_id": user_id}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))