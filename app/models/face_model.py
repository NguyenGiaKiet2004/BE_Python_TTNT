from typing import Optional, Tuple
import cv2
import dlib
import numpy as np
import pickle
import uuid
import logging
import os
from app.core import config

IS_USING_CUDA : bool = dlib.DLIB_USE_CUDA #check if the device supports CUDA, and properly compiled

class FaceModel:
    """
    Handles all face detection and recognition business logic using GPU-accelerated models.
    
    """

    def __init__(self):
        """
        Initializes Dlib's models (HOG-based face detector, or CNN-based if CUDA is available, shape predictor, and face recognition model).
        """
        
        
        if not IS_USING_CUDA:
            try:
                if not os.path.exists(config.SHAPE_PREDICTOR_PATH):
                    raise FileNotFoundError(f"Shape predictor model not found at: {config.SHAPE_PREDICTOR_PATH}")
                if not os.path.exists(config.FACE_REC_MODEL_PATH):
                    raise FileNotFoundError(f"Face recognition model not found at: {config.FACE_REC_MODEL_PATH}")

                logging.info("Initializing FaceModelV2 (cpu-Only)...")
                # Load HOG-based face detector (for CPU-only device)
                self.detector = dlib.get_frontal_face_detector()
                self.sp = dlib.shape_predictor(config.SHAPE_PREDICTOR_PATH)
                self.facerec = dlib.face_recognition_model_v1(config.FACE_REC_MODEL_PATH)

                self._parse_detections = lambda dets: dets

                logging.info("FaceModelV2 initialized successfully with CPU-only detector.")
            except Exception as e:
                logging.critical(f"Fatal error initializing FaceModelV2: {e}")
                raise RuntimeError("Cannot initialize Face Detection and Recognition Model.")
         
        else:
            try:
                logging.info("Initializing FaceModelV2 (GPU-Only)...")
            
                # Ensure required model files exist before attempting to load
                if not os.path.exists(config.CNN_DETECTOR_PATH):
                    raise FileNotFoundError(f"CNN face detector model not found at: {config.CNN_DETECTOR_PATH}")
                if not os.path.exists(config.SHAPE_PREDICTOR_PATH):
                    raise FileNotFoundError(f"Shape predictor model not found at: {config.SHAPE_PREDICTOR_PATH}")
                if not os.path.exists(config.FACE_REC_MODEL_PATH):
                    raise FileNotFoundError(f"Face recognition model not found at: {config.FACE_REC_MODEL_PATH}")

                # Load the CNN-based face detector (for GPU)
                self.detector = dlib.cnn_face_detection_model_v1(config.CNN_DETECTOR_PATH)                
                # Load the shape predictor and face recognition models
                self.sp = dlib.shape_predictor(config.SHAPE_PREDICTOR_PATH)
                self.facerec = dlib.face_recognition_model_v1(config.FACE_REC_MODEL_PATH)

                self._parse_detections = lambda dets: [d.rect for d in dets]

                logging.info("FaceModelV2 initialized successfully with CNN detector.")

            except Exception as e:
                logging.critical(f"Fatal error initializing FaceModelV2: {e}")

                raise RuntimeError("Could not load dlib's GPU models. Ensure CUDA is installed and model paths are correct.") from e

    def _load_encodings(self) -> dict:
        """Loads face encodings from the pickle file."""
        try:
            with open(config.ENCODINGS_DB_PATH, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:

            return {}

    def _save_encodings(self, encodings_data: dict) -> None:
        """Saves face encodings to the pickle file."""
        with open(config.ENCODINGS_DB_PATH, 'wb') as f:
            pickle.dump(encodings_data, f)

    def _get_single_face_encoding(self, image_bytes: bytes) -> Tuple[any, Optional[np.ndarray], Optional[dlib.rectangle]]:
        """
        A helper function to find exactly one face and return its details:
        the encoding, the original image array, and the face rectangle.
        """
        image_np = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image from bytes.")

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        dets = self.detector(rgb_img, 1)

        if len(dets) == 0:
            raise ValueError("No face detected in the image.")
        if len(dets) > 1:
            raise ValueError("Multiple faces detected. Only one face is allowed.")
        
        rects = self._parse_detections(dets) #This line ò code already distinguish the use ò CUDA
         
        face_rect = rects[0]

        shape = self.sp(rgb_img, face_rect)
        

        face_encoding = np.array(self.facerec.compute_face_descriptor(rgb_img, shape))
        
        return face_encoding, img, face_rect

    def register_new_face(self, image_bytes: bytes) -> Tuple[bool, Optional[uuid.UUID], Optional[str]]:
        """
        Processes an image, extracts encoding, saves it, and returns a new user ID.
        Also saves a cropped image of the detected face.
        """
        try:
            face_encoding, original_image, face_rect = self._get_single_face_encoding(image_bytes)
            
            known_encodings = self._load_encodings()
            new_face_id = uuid.uuid4()
            known_encodings[new_face_id] = face_encoding

            try:
                top, right, bottom, left = face_rect.top(), face_rect.right(), face_rect.bottom(), face_rect.left()
                padding = 20
                

                h, w, _ = original_image.shape
                top = max(0, top - padding)
                left = max(0, left - padding)
                bottom = min(h, bottom + padding)
                right = min(w, right + padding)
                
                cropped_face = original_image[top:bottom, left:right]
                
                filename = f"{new_face_id}.jpg"
                save_path = os.path.join(config.CROPPED_FACES_DIR, filename)
                

                os.makedirs(config.CROPPED_FACES_DIR, exist_ok=True)
                
                cv2.imwrite(save_path, cropped_face)
                logging.info(f"Successfully saved cropped face image to: {save_path}")
                self._save_encodings(known_encodings)          
                logging.info(f"Successfully registered new face with ID: {new_face_id}")
            except Exception as e:
                
                logging.error(f"Failed to save cropped face image for {new_face_id}: {e}")
                return True, new_face_id, None
        except:
            logging.error(f"Failed to register face for {new_face_id}: {e}")
            return False, None, None

        return True, new_face_id, save_path
    
    def delete_face(self, face_id_to_delete: uuid.UUID) -> bool:
        """
        Remove a Face from encoding database, (but not the cropped picture of the face)

        Args:
            face_id_to_delete (uuid.UUID): UUID of the Face to be deleted
        Returns:
            bool: 
        """
        known_encodings = self._load_encodings()

        if face_id_to_delete not in known_encodings:
            logging.warning(f"Attempted to delete a non-existent face_id: {face_id_to_delete}")
            return False

        try:
            del known_encodings[face_id_to_delete]
            self._save_encodings(known_encodings)
            logging.info(f"Successfully deleted encoding for face_id: {face_id_to_delete}")

            return True
        except Exception as e:
            logging.error(f"An error occurred while deleting face {face_id_to_delete}: {e}")
            return False
    
    def recognize_face(self, image_bytes: bytes) -> Tuple[bool, Optional[uuid.UUID]]:
        """
        Finds the closest match for a face in the database from an image (1-to-N comparison).
        """
        known_encodings_data = self._load_encodings()
        if not known_encodings_data:
            logging.warning("Encodings database is empty. Cannot perform recognition.")
            return (False, None)

        known_ids = list(known_encodings_data.keys())
        known_vectors = np.array(list(known_encodings_data.values()))

        unknown_encoding, _, _ = self._get_single_face_encoding(image_bytes)

        distances = np.linalg.norm(known_vectors - unknown_encoding, axis=1)
        
        best_match_index = np.argmin(distances)
        best_distance = distances[best_match_index]

        logging.info(f"Recognition attempt: Best match distance is {best_distance:.4f}")

        if best_distance <= config.FACE_RECOGNITION_TOLERANCE:
            matched_id = known_ids[best_match_index]
            logging.info(f"Match found for user ID: {matched_id}")
            return (True, matched_id)
        
        logging.info("No match found within tolerance.")
        return (False, None)
    
    def verify_face(self, image_bytes: bytes, face_id_to_verify: uuid.UUID) -> bool:
        """
        Verifies if a face matches a specific known face ID (1-to-1 comparison).
        """
        known_encodings_data = self._load_encodings()
        known_encoding = known_encodings_data.get(face_id_to_verify)

        if known_encoding is None:
            logging.warning(f"Verification attempted for non-existent face_id: {face_id_to_verify}")
            return False

        unknown_encoding, _, _ = self._get_single_face_encoding(image_bytes)
        
        distance = np.linalg.norm(known_encoding - unknown_encoding)
        
        is_match = distance <= config.FACE_RECOGNITION_TOLERANCE
        logging.info(f"Verification for {face_id_to_verify}: Distance={distance:.4f}, Match={is_match}")
        
        return is_match
    
face_model = FaceModel()