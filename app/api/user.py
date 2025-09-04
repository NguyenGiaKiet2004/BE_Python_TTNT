import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.sql_models import User, Department
from app.models.schemas import User as UserSchema, UserUpdateSchema
from app.core.security import get_current_user

router = APIRouter()

@router.get(
    "/me",
    response_model=UserSchema,
    summary="Get current user's details"
)
def get_current_user_details(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_with_department = db.query(User, Department.department_name).filter(
        User.user_id == user.user_id
    ).join(
        Department, User.department_id == Department.department_id, isouter=True
    ).first()

    if not user_with_department:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_obj, department_name = user_with_department
    
    response_data = user_obj.__dict__
    response_data['department_name'] = department_name

    return response_data

@router.put(
    "/me",
    response_model=UserSchema,
    summary="Update current user's details"
)
def update_user_details(
    updated_data: UserUpdateSchema,    # dùng schema riêng cho update, không cần bắt buộc đầy đủ
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)   # trả về SQLAlchemy model
):
    # Lấy user từ DB để chắc chắn nó thuộc session
    db_user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cập nhật các field
    if updated_data.full_name is not None:
        db_user.full_name = updated_data.full_name
    if updated_data.phone_number is not None:
        db_user.phone_number = updated_data.phone_number
    if updated_data.address is not None:
        db_user.address = updated_data.address

    db.commit()
    db.refresh(db_user)

    # Lấy tên phòng ban (nếu có)
    department_name = None
    if db_user.department_id:
        dep = db.query(Department.department_name).filter_by(department_id=db_user.department_id).first()
        department_name = dep[0] if dep else None

    # Chuẩn bị response
    response_data = db_user.__dict__.copy()
    response_data['department_name'] = department_name

    return response_data


# from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
# from sqlalchemy.orm import Session
# from app.models import sql_models, schemas
# from app.core.database import SessionLocal
# from app.core import security
# from app.core.security import get_current_user
# from app.core.exceptions import RegistrationError

# router = APIRouter(tags=["users"])

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @router.get("/me", response_model=schemas.User)
# def get_current_user_profile(current_user: schemas.User = Depends(get_current_user)):
#     return current_user

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