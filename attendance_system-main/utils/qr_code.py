import qrcode
import json
import os
from config import Config
import logging
from PIL import Image, ImageDraw, ImageFont

class QRCodeManager:
    def __init__(self):
        self.qr_codes_path = Config.QR_CODES_PATH
        os.makedirs(self.qr_codes_path, exist_ok=True)
    
    def generate_student_qr(self, student_data):
        """Generate QR code for a student with their details"""
        try:
            # Prepare QR code data
            qr_data = {
                'student_id': student_data['student_id'],
                'name': student_data['full_name'],
                'class': student_data['class_name'],
                'section': student_data['section'],
                'roll_number': student_data['roll_number'],
                'type': 'student_attendance'
            }
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Create ID card with QR code
            id_card = self.create_student_id_card(student_data, qr_img)
            
            # Save the ID card
            filename = f"{student_data['student_id']}_id_card.png"
            filepath = os.path.join(self.qr_codes_path, filename)
            id_card.save(filepath)
            
            return True, filename, json.dumps(qr_data)
            
        except Exception as e:
            logging.error(f"Error generating QR code: {e}")
            return False, None, None
    
    def create_student_id_card(self, student_data, qr_img):
        """Create a printable ID card with QR code and student details"""
        # ID card dimensions (in pixels, for 300 DPI printing)
        card_width, card_height = 1050, 650  # ~3.5" x 2.2"
        
        # Create card background
        card = Image.new('RGB', (card_width, card_height), 'white')
        draw = ImageDraw.Draw(card)
        
        # Colors
        header_color = '#2E86AB'
        text_color = '#333333'
        
        # Header
        draw.rectangle([0, 0, card_width, 100], fill=header_color)
        
        # School name (you can customize this)
        try:
            header_font = ImageFont.truetype("arial.ttf", 36)
            name_font = ImageFont.truetype("arial.ttf", 28)
            detail_font = ImageFont.truetype("arial.ttf", 20)
        except:
            header_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
        
        # Draw school name
        school_name = "SMART SCHOOL"
        draw.text((20, 30), school_name, fill='white', font=header_font)
        draw.text((20, 70), "STUDENT ID CARD", fill='white', font=detail_font)
        
        # Student photo area (placeholder)
        photo_area = [30, 130, 200, 300]
        draw.rectangle(photo_area, outline=header_color, width=3)
        draw.text((photo_area[0] + 10, photo_area[1] + 70), "STUDENT\nPHOTO", 
                 fill=header_color, font=detail_font, align="center")
        
        # Student details
        details_x = 230
        details_y = 140
        line_height = 35
        
        details = [
            f"Name: {student_data['full_name']}",
            f"Student ID: {student_data['student_id']}",
            f"Class: {student_data['class_name']}-{student_data['section']}",
            f"Roll No: {student_data['roll_number']}",
            f"Year: 2024-25"
        ]
        
        for i, detail in enumerate(details):
            draw.text((details_x, details_y + i * line_height), detail, 
                     fill=text_color, font=name_font)
        
        # QR Code
        qr_size = 150
        qr_resized = qr_img.resize((qr_size, qr_size))
        qr_position = (card_width - qr_size - 30, card_height - qr_size - 30)
        card.paste(qr_resized, qr_position)
        
        # QR Code label
        draw.text((qr_position[0], qr_position[1] - 25), "Scan for Attendance", 
                 fill=text_color, font=detail_font)
        
        # Footer
        draw.rectangle([0, card_height-50, card_width, card_height], fill=header_color)
        draw.text((20, card_height-35), "Emergency Contact: +91-9876543210", 
                 fill='white', font=detail_font)
        
        return card
    
    def decode_qr_data(self, qr_data_string):
        """Decode QR code data string"""
        try:
            data = json.loads(qr_data_string)
            if data.get('type') == 'student_attendance':
                return True, data
            else:
                return False, "Invalid QR code type"
        except json.JSONDecodeError:
            return False, "Invalid QR code data format"
        except Exception as e:
            logging.error(f"Error decoding QR data: {e}")
            return False, f"Error decoding QR code: {str(e)}"
    
    def batch_generate_qr_codes(self, students_data):
        """Generate QR codes for multiple students"""
        results = []
        for student in students_data:
            success, filename, qr_data = self.generate_student_qr(student)
            results.append({
                'student_id': student['student_id'],
                'success': success,
                'filename': filename,
                'qr_data': qr_data
            })
        return results

# Global QR code manager instance
qr_manager = QRCodeManager()
