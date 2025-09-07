"""
OCR Processor - Handles Optical Character Recognition for form processing
"""

import cv2
import pytesseract
import numpy as np
from PIL import Image
import json
import logging
from config import Config

class OCRProcessor:
    """Class to handle OCR operations for form processing"""
    
    def __init__(self):
        # Set Tesseract command path
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
        self.logger = logging.getLogger(__name__)
    
    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        image = None
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Could not read image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Clear original image from memory
            del image
            image = None
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Clear gray image from memory
            del gray
            
            # Apply threshold to get binary image
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Clear blurred image from memory
            del blurred
            
            # Morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Clear thresh image from memory
            del thresh
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {e}")
            # Ensure cleanup on error
            if image is not None:
                del image
            return None
    
    def extract_text_from_image(self, image_path, preprocess=True):
        """Extract text from image using OCR"""
        pil_image = None
        try:
            if preprocess:
                processed_image = self.preprocess_image(image_path)
                if processed_image is None:
                    return None, "Failed to preprocess image"
                
                # Convert back to PIL Image for tesseract
                pil_image = Image.fromarray(processed_image)
                
                # Clear processed image from memory
                del processed_image
            else:
                pil_image = Image.open(image_path)
            
            # Configure tesseract for better accuracy
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,/-:() '
            
            # Extract text
            text = pytesseract.image_to_string(pil_image, config=custom_config)
            
            return text.strip(), None
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image: {e}")
            return None, str(e)
        finally:
            # Ensure PIL image is cleaned up
            if pil_image is not None:
                pil_image.close()
    
    def extract_form_data(self, image_path):
        """Extract structured data from student enrollment form"""
        try:
            # Extract raw text
            text, error = self.extract_text_from_image(image_path)
            if error:
                return None, error
            
            if not text:
                return None, "No text found in image"
            
            # Parse form data based on expected fields
            form_data = self.parse_student_form(text)
            
            return form_data, None
            
        except Exception as e:
            self.logger.error(f"Error extracting form data: {e}")
            return None, str(e)
    
    def parse_student_form(self, text):
        """Parse student form text into structured data"""
        try:
            form_data = {}
            lines = text.split('\n')
            
            # Common field patterns
            field_patterns = {
                'student_name': ['name', 'student name', 'full name'],
                'father_name': ['father', 'father name', 'father\'s name'],
                'mother_name': ['mother', 'mother name', 'mother\'s name'],
                'roll_number': ['roll', 'roll no', 'roll number'],
                'student_id': ['student id', 'id', 'admission no'],
                'class': ['class', 'standard', 'grade'],
                'section': ['section', 'division'],
                'date_of_birth': ['dob', 'date of birth', 'birth date'],
                'address': ['address', 'residence'],
                'phone': ['phone', 'mobile', 'contact']
            }
            
            # Extract data using pattern matching
            for line in lines:
                line_lower = line.lower().strip()
                
                for field, patterns in field_patterns.items():
                    for pattern in patterns:
                        if pattern in line_lower:
                            # Extract value after the pattern
                            value = self.extract_value_after_pattern(line, pattern)
                            if value and field not in form_data:
                                form_data[field] = value
                            break
            
            # Clean and validate extracted data
            form_data = self.clean_form_data(form_data)
            
            return form_data
            
        except Exception as e:
            self.logger.error(f"Error parsing form data: {e}")
            return {}
    
    def extract_value_after_pattern(self, line, pattern):
        """Extract value that comes after a pattern in a line"""
        try:
            # Find pattern position
            pattern_pos = line.lower().find(pattern)
            if pattern_pos == -1:
                return None
            
            # Extract text after pattern
            after_pattern = line[pattern_pos + len(pattern):].strip()
            
            # Remove common separators
            separators = [':', '-', '=', '|']
            for sep in separators:
                if sep in after_pattern:
                    after_pattern = after_pattern.split(sep)[-1].strip()
            
            # Clean up the value
            value = after_pattern.strip()
            
            # Return if value is not empty and reasonable length
            if value and len(value) > 0 and len(value) < 100:
                return value
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting value: {e}")
            return None
    
    def clean_form_data(self, form_data):
        """Clean and validate extracted form data"""
        try:
            cleaned_data = {}
            
            for field, value in form_data.items():
                if not value:
                    continue
                
                # Clean the value
                cleaned_value = value.strip()
                
                # Field-specific cleaning
                if field in ['student_name', 'father_name', 'mother_name']:
                    # Remove numbers and special characters from names
                    cleaned_value = ''.join(c for c in cleaned_value if c.isalpha() or c.isspace())
                    cleaned_value = ' '.join(cleaned_value.split())  # Remove extra spaces
                
                elif field in ['roll_number', 'student_id']:
                    # Keep only alphanumeric characters
                    cleaned_value = ''.join(c for c in cleaned_value if c.isalnum())
                
                elif field == 'phone':
                    # Keep only digits
                    cleaned_value = ''.join(c for c in cleaned_value if c.isdigit())
                
                elif field == 'date_of_birth':
                    # Try to parse date format
                    cleaned_value = self.parse_date(cleaned_value)
                
                # Only add if cleaned value is not empty
                if cleaned_value:
                    cleaned_data[field] = cleaned_value
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error cleaning form data: {e}")
            return form_data
    
    def parse_date(self, date_string):
        """Parse date string into standard format"""
        try:
            import re
            from datetime import datetime
            
            # Common date patterns
            patterns = [
                r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
                r'(\d{2,4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})',  # YYYY/MM/DD
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_string)
                if match:
                    groups = match.groups()
                    try:
                        # Try different date formats
                        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d']:
                            try:
                                date_obj = datetime.strptime(f"{groups[0]}/{groups[1]}/{groups[2]}", fmt)
                                return date_obj.strftime('%Y-%m-%d')
                            except:
                                continue
                    except:
                        continue
            
            return date_string  # Return original if parsing fails
            
        except Exception as e:
            self.logger.error(f"Error parsing date: {e}")
            return date_string
    
    def validate_form_data(self, form_data):
        """Validate extracted form data"""
        try:
            validation_errors = []
            
            # Required fields
            required_fields = ['student_name', 'roll_number']
            for field in required_fields:
                if field not in form_data or not form_data[field]:
                    validation_errors.append(f"Missing required field: {field}")
            
            # Validate specific fields
            if 'student_name' in form_data:
                name = form_data['student_name']
                if len(name) < 2 or len(name) > 50:
                    validation_errors.append("Student name should be 2-50 characters long")
            
            if 'roll_number' in form_data:
                roll = form_data['roll_number']
                if not roll.isalnum() or len(roll) > 10:
                    validation_errors.append("Roll number should be alphanumeric and max 10 characters")
            
            if 'phone' in form_data and form_data['phone']:
                phone = form_data['phone']
                if len(phone) < 10 or len(phone) > 15:
                    validation_errors.append("Phone number should be 10-15 digits")
            
            return len(validation_errors) == 0, validation_errors
            
        except Exception as e:
            self.logger.error(f"Error validating form data: {e}")
            return False, [str(e)]
    
    def process_batch_forms(self, image_paths):
        """Process multiple form images in batch"""
        try:
            results = []
            
            for image_path in image_paths:
                form_data, error = self.extract_form_data(image_path)
                
                if error:
                    results.append({
                        'image_path': image_path,
                        'success': False,
                        'error': error,
                        'data': None
                    })
                else:
                    is_valid, validation_errors = self.validate_form_data(form_data)
                    results.append({
                        'image_path': image_path,
                        'success': True,
                        'error': None,
                        'data': form_data,
                        'is_valid': is_valid,
                        'validation_errors': validation_errors
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing batch forms: {e}")
            return []

# Global OCR processor instance
ocr_processor = OCRProcessor()
