import logging
from datetime import timedelta


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.models import sql_models
from app.models import schemas
from app.core.config import settings


router = APIRouter()

@router.post(
    "/auth/register",
    response_model=schemas.User,
    summary="Register a new user"
)
def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account with a hashed password.
    """
    db_user = db.query(sql_models.User).filter(sql_models.User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = security.get_password_hash(user_data.password)
    db_user = sql_models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logging.info(f"User {db_user.email} registered successfully with ID {db_user.user_id}.")
    return db_user

@router.post(
    "/auth/token",
    response_model=schemas.Token,
    summary="User login and get an access token"
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticates a user and returns a JWT access token.
    """
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logging.info(f"User {user.email} logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}