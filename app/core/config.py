import os
import face_recognition_models as frm
from pydantic_settings import BaseSettings

# Get paths to models automatically from the installed library
SHAPE_PREDICTOR_PATH = frm.pose_predictor_model_location()
FACE_REC_MODEL_PATH = frm.face_recognition_model_location()
CNN_DETECTOR_PATH = frm.cnn_face_detector_model_location()


# Define base directory for data and temporary uploads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

CROPPED_FACES_DIR = os.path.join(DATA_DIR, 'cropped_faces')
# Create necessary directories at startup
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CROPPED_FACES_DIR, exist_ok=True)

# Define face recognition tolerance
FACE_RECOGNITION_TOLERANCE = 0.6

# =======================================================
#Database configuration
# =======================================================
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./test.db"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()

