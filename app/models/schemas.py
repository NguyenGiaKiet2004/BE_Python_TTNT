from pydantic import BaseModel
from datetime import datetime, date

class UserBase(BaseModel):
    full_name: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: int
    role: str
    department_id: int | None = None
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class AttendanceRecordCreate(BaseModel):
    user_id: int
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    status: str | None = None
    record_date: date

class AttendanceRecord(AttendanceRecordCreate):
    record_id: int
    
    class Config:
        orm_mode = True

class FaceRegisterResponse(BaseModel):
    user_id: int

class RecognitionResponse(BaseModel):
    user_id: int
    full_name: str
    status: str