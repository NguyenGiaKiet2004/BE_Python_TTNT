from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    employee_id: str  # Thêm dòng này để schema có trường employee_id
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    address: Optional[str] = None
    
    class Config:
        orm_mode = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    password_confirm: str = Field(..., min_length=6)

    @validator('password_confirm', pre=True, always=True)
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

class User(UserBase):
    user_id: int
    role: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AttendanceRecordCreate(BaseModel):
    user_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[str] = None
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
    



class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


# from pydantic import BaseModel
# from datetime import datetime, date

# class UserBase(BaseModel):
#     full_name: str
#     email: str

# class UserCreate(UserBase):
#     password: str

# class User(UserBase):
#     user_id: int
#     role: str
#     department_id: int | None = None
    
#     class Config:
#         orm_mode = True

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     email: str | None = None

# class AttendanceRecordCreate(BaseModel):
#     user_id: int
#     check_in_time: datetime | None = None
#     check_out_time: datetime | None = None
#     status: str | None = None
#     record_date: date

# class AttendanceRecord(AttendanceRecordCreate):
#     record_id: int
    
#     class Config:
#         orm_mode = True

# class FaceRegisterResponse(BaseModel):
#     user_id: int

# class RecognitionResponse(BaseModel):
#     user_id: int
#     full_name: str
#     status: str