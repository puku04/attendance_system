import cv2
import face_recognition
import numpy as np
import pickle
import json
import os
from config import Config
import logging

class FaceRecognitionManager:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.tolerance = Config.FACE_RECOGNITION_TOLERANCE
        self.model = Config.FACE_DETECTION_MODEL
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known face encodings from file"""
        if os.path.exists(Config.FACE_ENCODINGS_PATH):
            try:
                with open(Config.FACE_ENCODINGS_PATH, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                    self.known_face_ids = data.get('ids', [])
                logging.info(f"Loaded {len(self.known_face_encodings)} known faces")
            except Exception as e:
                logging.error(f"Error loading face encodings: {e}")
    
    def save_known_faces(self):
        """Save known face encodings to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(Config.FACE_ENCODINGS_PATH), exist_ok=True)
            
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'ids': self.known_face_ids
            }
            with open(Config.FACE_ENCODINGS_PATH, 'wb') as f:
                pickle.dump(data, f)
            logging.info("Face encodings saved successfully")
        except Exception as e:
            logging.error(f"Error saving face encodings: {e}")
    
    def add_student_face(self, image_path, student_id, student_name):
        """Add a new student's face to the known faces"""
        try:
            # Load and encode the face
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image, model=self.model)
            
            if len(face_encodings) == 0:
                return False, "No face detected in the image"
            
            if len(face_encodings) > 1:
                return False, "Multiple faces detected. Please provide an image with a single face"
            
            # Add to known faces
            face_encoding = face_encodings[0]
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(student_name)
            self.known_face_ids.append(student_id)
            
            # Save to file
            self.save_known_faces()
            
            return True, "Face added successfully"
            
        except Exception as e:
            logging.error(f"Error adding student face: {e}")
            return False, f"Error processing face: {str(e)}"
    
    def recognize_faces_in_image(self, image_path):
        """Recognize all faces in a group photo"""
        try:
            # Load the uploaded image
            image = face_recognition.load_image_file(image_path)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_image, model=self.model)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations, model=self.model)
            
            recognized_students = []
            unrecognized_faces = len(face_encodings)
            
            for face_encoding in face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, face_encoding, tolerance=self.tolerance
                )
                distances = face_recognition.face_distance(
                    self.known_face_encodings, face_encoding
                )
                
                if len(distances) > 0 and True in matches:
                    best_match_index = np.argmin(distances)
                    if matches[best_match_index]:
                        student_id = self.known_face_ids[best_match_index]
                        student_name = self.known_face_names[best_match_index]
                        confidence = 1 - distances[best_match_index]
                        
                        recognized_students.append({
                            'student_id': student_id,
                            'student_name': student_name,
                            'confidence': float(confidence)
                        })
                        unrecognized_faces -= 1
            
            return {
                'success': True,
                'total_faces_detected': len(face_encodings),
                'recognized_students': recognized_students,
                'unrecognized_faces': unrecognized_faces
            }
            
        except Exception as e:
            logging.error(f"Error in face recognition: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_faces_detected': 0,
                'recognized_students': [],
                'unrecognized_faces': 0
            }
    
    def update_student_face(self, student_id, new_image_path):
        """Update an existing student's face encoding"""
        try:
            # Find and remove existing encoding
            if student_id in self.known_face_ids:
                index = self.known_face_ids.index(student_id)
                self.known_face_encodings.pop(index)
                name = self.known_face_names.pop(index)
                self.known_face_ids.pop(index)
                
                # Add new encoding
                success, message = self.add_student_face(new_image_path, student_id, name)
                return success, message
            else:
                return False, "Student not found in face database"
                
        except Exception as e:
            logging.error(f"Error updating student face: {e}")
            return False, f"Error updating face: {str(e)}"
    
    def remove_student_face(self, student_id):
        """Remove a student's face from the database"""
        try:
            if student_id in self.known_face_ids:
                index = self.known_face_ids.index(student_id)
                self.known_face_encodings.pop(index)
                self.known_face_names.pop(index)
                self.known_face_ids.pop(index)
                self.save_known_faces()
                return True, "Face removed successfully"
            else:
                return False, "Student not found in face database"
                
        except Exception as e:
            logging.error(f"Error removing student face: {e}")
            return False, f"Error removing face: {str(e)}"

# Global face recognition instance
face_manager = FaceRecognitionManager()
