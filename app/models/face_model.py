from typing import Optional, Tuple
import cv2
import dlib
import numpy as np
import logging
import os
from sqlalchemy.orm import Session
from app.core import config
from app.models import sql_models
from app.core.database import SessionLocal

class FaceModel:
    """Handles all face detection and recognition business logic."""

    def __init__(self):
        """Initializes Dlib models."""
        try:
            self.detector = dlib.get_frontal_face_detector()
            self.sp = dlib.shape_predictor(config.SHAPE_PREDICTOR_PATH)
            self.facerec = dlib.face_recognition_model_v1(config.FACE_REC_MODEL_PATH)
            logging.info("FaceModel initialized successfully.")
        except Exception as e:
            logging.critical(f"Fatal error initializing FaceModel: {e}")
            raise RuntimeError("Could not load dlib models.") from e

    def _get_single_face_encoding(self, image_bytes: bytes) -> tuple:
        """
        A helper function to find exactly one face and return its details:
        the encoding, the original image array, and the face rectangle.
        """
        image_np = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image.")

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        dets = self.detector(rgb_img, 1)

        if len(dets) == 0:
            raise ValueError("No face detected.")
        if len(dets) > 1:
            raise ValueError("Multiple faces detected.")

        face_rect = dets[0]
        shape = self.sp(rgb_img, face_rect)
        face_encoding = np.array(self.facerec.compute_face_descriptor(rgb_img, shape))
        
        return face_encoding, img, face_rect

    def register_new_face(self, user_id: int, image_bytes: bytes) -> None:
        """
        Processes an image, extracts encoding, and saves it to the database.

        Args:
            user_id: The ID of the user to register the face for.
            image_bytes: The image file in bytes.
        
        Raises:
            ValueError: If no face or multiple faces are detected.
        """
        db: Session = SessionLocal()
        try:
            face_encoding, original_image, face_rect = self._get_single_face_encoding(image_bytes)

            # Lưu vào database
            new_face_data = sql_models.FacialData(
                user_id=user_id,
                encoding_data=face_encoding.tobytes(), # Convert numpy array to bytes
                reference_image_url=f"/static/faces/{user_id}.jpg" # Example URL
            )
            db.add(new_face_data)
            db.commit()
            logging.info(f"Successfully registered new face for user ID: {user_id}")

            # Optionally, save cropped face image to disk
            top, right, bottom, left = face_rect.top(), face_rect.right(), face_rect.bottom(), face_rect.left()
            cropped_face = original_image[max(0, top-20):bottom+20, max(0, left-20):right+20]
            filename = f"{user_id}.jpg"
            save_path = os.path.join(config.CROPPED_FACES_DIR, filename)
            cv2.imwrite(save_path, cropped_face)
            logging.info(f"Successfully saved cropped face image to: {save_path}")

        finally:
            db.close()

    def recognize_face(self, image_bytes: bytes) -> Tuple[bool, Optional[int]]:
        """
        Finds the closest match for a face in the database from an image.
        """
        db: Session = SessionLocal()
        try:
            # Lấy tất cả encodings từ database
            known_encodings_data = db.query(sql_models.FacialData).all()
            if not known_encodings_data:
                logging.warning("Encodings database is empty. Cannot perform recognition.")
                return (False, None)
            
            known_ids = [data.user_id for data in known_encodings_data]
            known_vectors = np.array([np.frombuffer(data.encoding_data) for data in known_encodings_data])
            
            # Xử lý ảnh đầu vào
            unknown_encoding, _, _ = self._get_single_face_encoding(image_bytes)
            
            # So sánh với các khuôn mặt đã biết
            distances = np.linalg.norm(known_vectors - unknown_encoding, axis=1)
            best_match_index = np.argmin(distances)
            best_distance = distances[best_match_index]
            
            logging.info(f"Best match distance: {best_distance}")
            
            if best_distance <= config.FACE_RECOGNITION_TOLERANCE:
                matched_id = known_ids[best_match_index]
                logging.info(f"Match found for user ID: {matched_id}")
                return (True, matched_id)
            
            logging.info("No match found within tolerance.")
            return (False, None)
            
        finally:
            db.close()

    def verify_face(self, image_bytes: bytes, user_id_to_verify: int) -> bool:
        """Verifies if a face matches a specific known face ID (1-to-1 comparison)."""
        db: Session = SessionLocal()
        try:
            # Lấy encoding của user_id cụ thể từ database
            known_face_data = db.query(sql_models.FacialData).filter(
                sql_models.FacialData.user_id == user_id_to_verify
            ).first()

            if known_face_data is None:
                logging.warning(f"Verification attempted for non-existent user_id: {user_id_to_verify}")
                return False
            
            known_encoding = np.frombuffer(known_face_data.encoding_data)
            
            unknown_encoding, _, _ = self._get_single_face_encoding(image_bytes)
            
            distance = np.linalg.norm(known_encoding - unknown_encoding)
            
            return distance <= config.FACE_RECOGNITION_TOLERANCE

        finally:
            db.close()


# Instantiate the model once to be reused across the application
face_model_instance = FaceModel()