from pydantic import BaseModel, EmailStr

# Dùng cho signup
class UserCreate(BaseModel):
    staff_id: str
    username: str
    password: str
    confirm_password: str
    email: EmailStr
    phone: str

# Dùng cho login
class UserLogin(BaseModel):
    username: str
    password: str
