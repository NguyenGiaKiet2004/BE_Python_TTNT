from pydantic import BaseModel, Field
from typing import Optional
import uuid

class FaceRegisterSuccessResponse(BaseModel):
    """Defines the successful registration response schema."""
    status: str = "success"
    message: str = "New User FACE registered successfully."
    user_id: str = Field(..., description="The unique ID assigned to the new user.")

    class Config:
        # Example for documentation
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "User registered successfully.",
                "user_id": "XXXXXX"
            }
        }
    
class VerifyResponse(BaseModel):
    """
    Defines the verification response schema.
    """
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