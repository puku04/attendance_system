"""
API Routes - RESTful API endpoints for the attendance system
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import logging
from models.student import StudentModel
from models.attendance import AttendanceModel
from models.user import UserModel
from utils.face_recognition import face_manager
from utils.qr_code import qr_manager
from utils.ocr_processor import ocr_processor
from utils.file_validator import file_validator

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

def api_login_required(f):
    """Decorator to require login for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def api_role_required(role):
    """Decorator to require specific role for API endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Student Management API
@api_bp.route('/students', methods=['GET'])
@api_login_required
def get_students():
    """Get all students"""
    try:
        class_id = request.args.get('class_id')
        
        if class_id:
            students = StudentModel.get_students_by_class(int(class_id))
        else:
            students = StudentModel.get_all_students()
        
        return jsonify({
            'success': True,
            'students': students
        })
        
    except Exception as e:
        logging.error(f"Error getting students: {e}")
        return jsonify({'success': False, 'error': 'Failed to get students'}), 500

@api_bp.route('/students/<student_id>', methods=['GET'])
@api_login_required
def get_student(student_id):
    """Get specific student"""
    try:
        student = StudentModel.get_student_by_id(student_id)
        
        if student:
            return jsonify({
                'success': True,
                'student': student
            })
        else:
            return jsonify({'success': False, 'error': 'Student not found'}), 404
            
    except Exception as e:
        logging.error(f"Error getting student: {e}")
        return jsonify({'success': False, 'error': 'Failed to get student'}), 500

@api_bp.route('/students/<student_id>', methods=['PUT'])
@api_login_required
@api_role_required('principal')
def update_student(student_id):
    """Update student information"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        success, message = StudentModel.update_student(student_id, data)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logging.error(f"Error updating student: {e}")
        return jsonify({'success': False, 'error': 'Failed to update student'}), 500

@api_bp.route('/students/<student_id>', methods=['DELETE'])
@api_login_required
@api_role_required('principal')
def delete_student(student_id):
    """Delete student"""
    try:
        success, message = StudentModel.delete_student(student_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logging.error(f"Error deleting student: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete student'}), 500

# Attendance API
@api_bp.route('/attendance', methods=['POST'])
@api_login_required
@api_role_required('teacher')
def mark_attendance():
    """Mark attendance for a student"""
    try:
        data = request.get_json()
        
        required_fields = ['student_id', 'class_id', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        success, message = AttendanceModel.mark_attendance(
            student_id=data['student_id'],
            class_id=data['class_id'],
            teacher_id=session['user_id'],
            status=data['status'],
            method=data.get('method', 'manual'),
            confidence_score=data.get('confidence_score'),
            photo_filename=data.get('photo_filename'),
            notes=data.get('notes')
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logging.error(f"Error marking attendance: {e}")
        return jsonify({'success': False, 'error': 'Failed to mark attendance'}), 500

@api_bp.route('/attendance/<int:class_id>', methods=['GET'])
@api_login_required
def get_class_attendance(class_id):
    """Get attendance for a specific class"""
    try:
        date_str = request.args.get('date')
        if not date_str:
            from datetime import date
            date_str = date.today().strftime('%Y-%m-%d')
        
        attendance = AttendanceModel.get_attendance_by_date(class_id, date_str)
        
        return jsonify({
            'success': True,
            'attendance': attendance,
            'date': date_str
        })
        
    except Exception as e:
        logging.error(f"Error getting class attendance: {e}")
        return jsonify({'success': False, 'error': 'Failed to get attendance'}), 500

@api_bp.route('/attendance/summary/<int:class_id>', methods=['GET'])
@api_login_required
def get_attendance_summary(class_id):
    """Get attendance summary for a class"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Start date and end date required'}), 400
        
        summary = AttendanceModel.get_attendance_summary(class_id, start_date, end_date)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logging.error(f"Error getting attendance summary: {e}")
        return jsonify({'success': False, 'error': 'Failed to get attendance summary'}), 500

# Face Recognition API
@api_bp.route('/face-recognition/process', methods=['POST'])
@api_login_required
@api_role_required('teacher')
def process_face_recognition():
    """Process face recognition for attendance"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Validate file
        is_valid, error_msg, file_info = file_validator.validate_file(
            file, 
            allowed_types=['image/jpeg', 'image/png', 'image/gif']
        )
        
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Save temporary file
        import os
        from config import Config
        
        filename = file_validator.sanitize_filename(file.filename)
        temp_path = file_validator.get_safe_path(
            os.path.join(Config.UPLOAD_FOLDER, 'temp'), 
            filename
        )
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        # Process face recognition
        result = face_manager.recognize_faces_in_image(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error processing face recognition: {e}")
        return jsonify({'success': False, 'error': 'Failed to process face recognition'}), 500

@api_bp.route('/face-recognition/add-student', methods=['POST'])
@api_login_required
@api_role_required('principal')
def add_student_face():
    """Add student face to recognition database"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        
        if not student_id or not student_name:
            return jsonify({'success': False, 'error': 'Student ID and name required'}), 400
        
        # Validate file
        is_valid, error_msg, file_info = file_validator.validate_file(
            file, 
            allowed_types=['image/jpeg', 'image/png', 'image/gif']
        )
        
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Save temporary file
        import os
        from config import Config
        
        filename = file_validator.sanitize_filename(file.filename)
        temp_path = file_validator.get_safe_path(
            os.path.join(Config.UPLOAD_FOLDER, 'temp'), 
            filename
        )
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        # Add face to recognition database
        success, message = face_manager.add_student_face(temp_path, student_id, student_name)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logging.error(f"Error adding student face: {e}")
        return jsonify({'success': False, 'error': 'Failed to add student face'}), 500

# QR Code API
@api_bp.route('/qr-codes/generate', methods=['POST'])
@api_login_required
@api_role_required('principal')
def generate_qr_codes():
    """Generate QR codes for students"""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        
        if not class_id:
            return jsonify({'success': False, 'error': 'Class ID required'}), 400
        
        # Get students in class
        students = StudentModel.get_students_by_class(class_id)
        
        if not students:
            return jsonify({'success': False, 'error': 'No students found in class'}), 404
        
        # Generate QR codes
        results = []
        for student in students:
            success, filename, qr_data = qr_manager.generate_student_qr(student)
            results.append({
                'student_id': student['student_id'],
                'success': success,
                'filename': filename,
                'qr_data': qr_data
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logging.error(f"Error generating QR codes: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate QR codes'}), 500

# OCR API
@api_bp.route('/ocr/process-form', methods=['POST'])
@api_login_required
@api_role_required('principal')
def process_form_ocr():
    """Process student enrollment form using OCR"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'}), 400
        
        # Save temporary file
        import os
        from werkzeug.utils import secure_filename
        from config import Config
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(Config.UPLOAD_FOLDER, 'temp', filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        # Process OCR
        form_data, error = ocr_processor.extract_form_data(temp_path)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        # Validate form data
        is_valid, validation_errors = ocr_processor.validate_form_data(form_data)
        
        return jsonify({
            'success': True,
            'form_data': form_data,
            'is_valid': is_valid,
            'validation_errors': validation_errors
        })
        
    except Exception as e:
        logging.error(f"Error processing form OCR: {e}")
        return jsonify({'success': False, 'error': 'Failed to process form'}), 500

# Dashboard Statistics API
@api_bp.route('/dashboard/stats', methods=['GET'])
@api_login_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        from utils.database import db
        from datetime import date
        
        stats = {}
        
        # Total students
        query = "SELECT COUNT(*) as count FROM students WHERE is_active = TRUE"
        result = db.execute_query(query)
        stats['total_students'] = result[0]['count'] if result else 0
        
        # Total teachers
        query = "SELECT COUNT(*) as count FROM users WHERE role = 'teacher' AND is_active = TRUE"
        result = db.execute_query(query)
        stats['total_teachers'] = result[0]['count'] if result else 0
        
        # Total classes
        query = "SELECT COUNT(*) as count FROM classes WHERE is_active = TRUE"
        result = db.execute_query(query)
        stats['total_classes'] = result[0]['count'] if result else 0
        
        # Today's attendance
        today = date.today()
        query = "SELECT COUNT(*) as count FROM attendance WHERE attendance_date = %s"
        result = db.execute_query(query, (today,))
        stats['today_attendance'] = result[0]['count'] if result else 0
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500

# Export API
@api_bp.route('/export/attendance', methods=['GET'])
@api_login_required
def export_attendance():
    """Export attendance data"""
    try:
        class_id = request.args.get('class_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'csv')
        
        if not all([class_id, start_date, end_date]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        # Get attendance summary
        summary = AttendanceModel.get_attendance_summary(int(class_id), start_date, end_date)
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Student ID', 'Name', 'Roll Number', 'Total Days', 'Present Days', 'Absent Days', 'Attendance %'])
            
            # Write data
            for record in summary:
                writer.writerow([
                    record['student_id'],
                    record['full_name'],
                    record['roll_number'],
                    record['total_days'],
                    record['present_days'],
                    record['absent_days'],
                    record['attendance_percentage']
                ])
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=attendance_{class_id}_{start_date}_{end_date}.csv'}
            )
        
        else:
            return jsonify({'success': False, 'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logging.error(f"Error exporting attendance: {e}")
        return jsonify({'success': False, 'error': 'Failed to export attendance'}), 500
