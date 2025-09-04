# ========================================================
# ▼▼▼ DÙNG ĐOẠN CODE NÀY CHO ENDPOINT /auth/register ▼▼▼
# ========================================================
import logging
from datetime import timedelta
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.models import sql_models
from app.models.face_model import face_model_instance, FaceModel
from app.models.schemas import UserCreate, User as UserSchema, Token
from fastapi.security import OAuth2PasswordRequestForm

# Các map phòng ban của bạn
manager_id_to_department_map = {
    '10000': {'department_id': 1, 'department_name': 'Phòng Kỹ thuật'},
    '20000': {'department_id': 2, 'department_name': 'Phòng Nhân sự'},
    '30000': {'department_id': 3, 'department_name': 'Phòng Marketing'},
    '40000': {'department_id': 4, 'department_name': 'Phòng Tài chính'},
}
employee_id_prefix_to_department_map = {
    '1': 1, '2': 2, '3': 3, '4': 4,
}

router = APIRouter()

def get_face_model() -> FaceModel:
    return face_model_instance

@router.post("/auth/register", summary="Register a new user with face image")
async def register_user_with_face(
    # --- Nhận tất cả thông tin từ form ---
    employee_id: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    phone_number: str = Form(None),
    address: str = Form(None),

    # --- Nhận file ảnh ---
    face_image: UploadFile = File(..., alias="faceImage"), # alias khớp với Kotlin

    # --- Dependencies ---
    db: Session = Depends(get_db),
    face_model: FaceModel = Depends(get_face_model)
):
    # 1. --- KIỂM TRA DỮ LIỆU ĐẦU VÀO ---
    if password != password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    if face_image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    db_user_email = db.query(sql_models.User).filter(sql_models.User.email == email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # 2. --- LOGIC PHÂN CHIA VAI TRÒ & PHÒNG BAN ---
    department_id = None
    role = "employee"
    if employee_id in manager_id_to_department_map:
        department_id = manager_id_to_department_map[employee_id]['department_id']
        role = "hr_manager"
    else:
        employee_id_prefix = employee_id[0]
        department_id = employee_id_prefix_to_department_map.get(employee_id_prefix)
        if not department_id:
            raise HTTPException(status_code=400, detail="Invalid Employee ID.")

    try:
        # 3. --- TẠO USER MỚI TRONG DATABASE ---
        hashed_password = security.get_password_hash(password)
        new_user = sql_models.User(
            employee_id=employee_id,
            full_name=full_name,
            email=email,
            password_hash=hashed_password, # Đảm bảo tên cột là 'password_hash'
            phone_number=phone_number,
            address=address,
            department_id=department_id,
            role=role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logging.info(f"Successfully created user with ID: {new_user.user_id}")

        # 4. --- ĐĂNG KÝ KHUÔN MẶT CHO USER VỪA TẠO ---
        image_bytes = await face_image.read()
        face_model.register_new_face(user_id=new_user.user_id, image_bytes=image_bytes)
        logging.info(f"Successfully registered face for user ID: {new_user.user_id}")

        # 5. --- TRẢ VỀ KẾT QUẢ ---
        department = db.query(sql_models.Department).filter_by(department_id=department_id).first()
        department_name = department.department_name if department else None

        return {
            "user_id": new_user.user_id,
            "employee_id": new_user.employee_id,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "phone_number": new_user.phone_number,
            "address": new_user.address,
            "role": new_user.role,
            "department_id": new_user.department_id,
            "department_name": department_name
        }
    except ValueError as ve:
        db.rollback()
        logging.warning(f"Face registration error: {ve}. Rolled back user creation.")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        logging.error(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@router.post(
    "/auth/token",
    response_model=Token,
    summary="User login and get an access token"
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logging.info(f"User {user.email} logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}

# import logging
# from datetime import timedelta
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.core import security
# from app.models import sql_models
# from app.models.schemas import UserCreate, User as UserSchema, Token

# router = APIRouter()

# @router.post(
#     "/auth/register",
#     response_model=UserSchema,
#     status_code=status.HTTP_201_CREATED,
#     summary="Register a new user"
# )
# def register_user(
#     user_data: UserCreate,
#     db: Session = Depends(get_db)
# ):
#     db_user = db.query(sql_models.User).filter(sql_models.User.email == user_data.email).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     hashed_password = security.get_password_hash(user_data.password)
#     db_user = sql_models.User(
#         full_name=user_data.full_name,
#         email=user_data.email,
#         password_hash=hashed_password,
#         phone_number=user_data.phone_number,
#         address=user_data.address
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     logging.info(f"User {db_user.email} registered successfully with ID {db_user.user_id}.")
#     return db_user

# @router.post(
#     "/auth/token",
#     response_model=Token,
#     summary="User login and get an access token"
# )
# def login_for_access_token(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     user = security.authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=security.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = security.create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
#     logging.info(f"User {user.email} logged in successfully.")
#     return {"access_token": access_token, "token_type": "bearer"}

# import logging
# from datetime import timedelta


# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.core import security
# from app.models import sql_models
# from app.models import schemas
# from app.core.config import settings


# router = APIRouter()

# @router.post(
#     "/auth/register",
#     response_model=schemas.User,
#     summary="Register a new user"
# )
# def register_user(
#     user_data: schemas.UserCreate,
#     db: Session = Depends(get_db)
# ):
#     """
#     Registers a new user account with a hashed password.
#     """
#     db_user = db.query(sql_models.User).filter(sql_models.User.email == user_data.email).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")

#     hashed_password = security.get_password_hash(user_data.password)
#     db_user = sql_models.User(
#         full_name=user_data.full_name,
#         email=user_data.email,
#         password_hash=hashed_password
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     logging.info(f"User {db_user.email} registered successfully with ID {db_user.user_id}.")
#     return db_user

# @router.post(
#     "/auth/token",
#     response_model=schemas.Token,
#     summary="User login and get an access token"
# )
# def login_for_access_token(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db)
# ):
#     """
#     Authenticates a user and returns a JWT access token.
#     """
#     user = security.authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = security.create_access_token(
#         data={"sub": user.email}, expires_delta=access_token_expires
#     )
#     logging.info(f"User {user.email} logged in successfully.")
#     return {"access_token": access_token, "token_type": "bearer"}