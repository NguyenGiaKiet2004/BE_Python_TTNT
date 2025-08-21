from pydantic import BaseModel, Field
from typing import Optional
import uuid

class RegisterSuccessResponse(BaseModel):
    """Defines the successful registration response schema."""
    user_id: uuid.UUID = Field(..., description="The unique ID assigned to the new user.")
    
class VerifyResponse(BaseModel):
    """Defines the verification response schema."""
    verified: bool = Field(..., description="True if the face matches the given face_id.")

class RecognizeResponse(BaseModel):
    """Defines the recognition response schema."""
    match: bool = Field(..., description="True if a match was found, otherwise False.")
    user_id: Optional[uuid.UUID] = Field(None, description="The unique ID of the matched user. Null if no match.")
    
# Thêm các schemas mới để đồng bộ với lỗi và logic đã sửa
class FaceRegisterResponse(BaseModel):
    user_id: int

class RecognitionResponse(BaseModel):
    user_id: Optional[int] = None
    full_name: Optional[str] = None
    status: str