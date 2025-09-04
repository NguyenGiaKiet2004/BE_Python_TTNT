# import logging
# from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
# from sqlalchemy.orm import Session

# # Giả sử bạn có các module này để xử lý database và face model
# from app.core.database import get_db # Hàm để lấy session database
# from app.core.security import get_password_hash # Hàm để hash mật khẩu
# from app.models import sql_models # Các model SQLAlchemy của bạn
# from app.models.face_model import face_model_instance, FaceModel # Model xử lý khuôn mặt

# router = APIRouter()

# def get_face_model() -> FaceModel:
#     """Dependency injection cho FaceModel instance."""
#     return face_model_instance

# # ===================================================================
# # ▼▼▼ ENDPOINT ĐĂNG KÝ MỚI CẦN THAY ĐỔI NẰM Ở ĐÂY ▼▼▼
# # ===================================================================
# @router.post("/auth/register", summary="Register a new user with face image")
# async def register_user_with_face(
#     # --- Nhận tất cả thông tin từ form ---
#     employee_id: str = Form(..., description="Employee's ID code"),
#     full_name: str = Form(..., description="User's full name"),
#     email: str = Form(..., description="User's email"),
#     password: str = Form(..., description="User's password"),
#     password_confirm: str = Form(..., description="Password confirmation"),
#     phone_number: str = Form(None, description="User's phone number"),
#     address: str = Form(None, description="User's address"),
    
#     # --- Nhận file ảnh ---
#     face_image: UploadFile = File(..., description="An image file (JPG or PNG) of the user's face."),
    
#     # --- Dependencies ---
#     db: Session = Depends(get_db),
#     face_model: FaceModel = Depends(get_face_model)
# ):
#     """
#     Tạo một người dùng mới với đầy đủ thông tin cá nhân và
#     đăng ký khuôn mặt của họ trong cùng một lần gọi API.
#     """
#     # 1. --- KIỂM TRA DỮ LIỆU ĐẦU VÀO ---
#     if password != password_confirm:
#         raise HTTPException(status_code=400, detail="Passwords do not match.")

#     if face_image.content_type not in ["image/jpeg", "image/png"]:
#         raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG.")

#     db_user_by_email = db.query(sql_models.User).filter(sql_models.User.email == email).first()
#     if db_user_by_email:
#         raise HTTPException(status_code=400, detail="Email already registered.")

#     db_user_by_id = db.query(sql_models.User).filter(sql_models.User.employee_id == employee_id).first()
#     if db_user_by_id:
#         raise HTTPException(status_code=400, detail="Employee ID already registered.")

#     try:
#         # 2. --- TẠO USER MỚI TRONG DATABASE ---
#         hashed_password = get_password_hash(password)
#         new_user = sql_models.User(
#             employee_id=employee_id,
#             full_name=full_name,
#             email=email,
#             hashed_password=hashed_password, # Lưu mật khẩu đã hash
#             phone_number=phone_number,
#             address=address,
#             role="employee" # Gán vai trò mặc định
#         )
#         db.add(new_user)
#         db.commit()
#         db.refresh(new_user) # Lấy lại thông tin user vừa tạo, bao gồm cả user_id mới

#         logging.info(f"Successfully created user with ID: {new_user.user_id}")

#         # 3. --- ĐĂNG KÝ KHUÔN MẶT CHO USER VỪA TẠO ---
#         image_bytes = await face_image.read()
        
#         # Gọi hàm xử lý khuôn mặt với user_id vừa được tạo
#         face_model.register_new_face(user_id=new_user.user_id, image_bytes=image_bytes)
        
#         logging.info(f"Successfully registered face for user ID: {new_user.user_id}")

#         # 4. --- TRẢ VỀ KẾT QUẢ THÀNH CÔNG ---
#         # Trả về thông tin user giống như DTO `RegisterResponseDto` bên phía Android
#         return {
#             "user_id": new_user.user_id,
#             "employee_id": new_user.employee_id,
#             "full_name": new_user.full_name,
#             "email": new_user.email,
#             "phone_number": new_user.phone_number,
#             "address": new_user.address,
#             "role": new_user.role
#         }

#     except ValueError as ve:
#         # Xóa user vừa tạo nếu đăng ký khuôn mặt thất bại để tránh rác database
#         db.delete(new_user)
#         db.commit()
#         logging.warning(f"Face registration validation error: {ve}. Rolled back user creation.")
#         raise HTTPException(status_code=400, detail=str(ve))
#     except Exception as e:
#         db.rollback() # Rollback nếu có lỗi xảy ra
#         logging.error(f"An unexpected error occurred during registration: {e}")
#         raise HTTPException(status_code=500, detail="An internal server error occurred.")
    
# # import logging
# # from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
# # from app.models.face_model import face_model_instance, FaceModel
# # from app.schemas.response import FaceRegisterResponse

# # router = APIRouter()

# # def get_face_model() -> FaceModel:
# #     """Dependency injection for the FaceModel instance."""
# #     return face_model_instance

# # @router.post(
# #     "/register",
# #     response_model=FaceRegisterResponse,
# #     summary="Register a New Face for a specific user"
# # )
# # async def register_face_endpoint(
# #     user_id: int = Form(..., description="The ID of the user to register the face for."),
# #     file: UploadFile = File(..., description="An image file (JPG or PNG) containing one face."),
# #     model: FaceModel = Depends(get_face_model)
# # ):
# #     """
# #     Receives an image and a user_id, processes the image to extract facial data,
# #     and stores it in the database.
# #     """
# #     if file.content_type not in ["image/jpeg", "image/png"]:
# #         raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG image.")

# #     try:
# #         image_bytes = await file.read()
# #         model.register_new_face(user_id=user_id, image_bytes=image_bytes)
# #         return FaceRegisterResponse(user_id=user_id)
# #     except ValueError as e:
# #         logging.warning(f"Registration validation error: {e}")
# #         raise HTTPException(status_code=400, detail=str(e))
# #     except Exception as e:
# #         logging.error(f"An unexpected error occurred during registration: {e}")
# #         raise HTTPException(status_code=500, detail="An internal server error occurred.")

