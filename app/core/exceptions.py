from fastapi import HTTPException, status

class RegistrationError(HTTPException):
    """Custom exception for registration-related errors."""
    def __init__(self, detail: str = "Registration failed"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class UserNotFound(HTTPException):
    """Custom exception for when a user is not found."""
    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)