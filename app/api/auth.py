from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..schemas.user_schema import UserCreate, UserLogin
from ..crud import user_crud
from ..core.config import SessionLocal, Base, engine
from ..models import user_model

Base.metadata.create_all(bind=engine)

# Chỉ prefix "auth" ở router
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if db.query(user_model.User).filter(user_model.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = user_crud.create_user(db, user)
    return {"message": "User created", "username": new_user.username}

@router.post("/signin")
def signin(user: UserLogin, db: Session = Depends(get_db)):
    db_user = user_crud.authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login success", "username": db_user.username}
