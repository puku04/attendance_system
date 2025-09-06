"""
Principal Routes - Handles principal-specific functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.student import StudentModel
from models.attendance import AttendanceModel
from models.user import UserModel
from utils.face_recognition import face_manager
from utils.qr_code import qr_manager
from utils.ocr_processor import ocr_processor
from utils.database import db
from datetime import date, datetime
import logging
import os
from werkzeug.utils import secure_filename

# Create principal blueprint
principal_bp = Blueprint('principal', __name__, url_prefix='/principal')

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'principal':
            flash('Access denied. Principal access required.', 'error')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@principal_bp.route('/dashboard')
@login_required
def dashboard():
    """Principal dashboard"""
    try:
        # Get dashboard statistics
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
        
        # Recent attendance sessions
        query = """
            SELECT s.*, c.class_name, c.section, u.full_name as teacher_name
            FROM attendance_sessions s
            JOIN classes c ON s.class_id = c.id
            JOIN users u ON s.teacher_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 10
        """
        recent_sessions = db.execute_query(query) or []
        
        # Class-wise attendance summary
        query = """
            SELECT c.class_name, c.section, COUNT(DISTINCT s.id) as total_students,
                   COUNT(DISTINCT a.student_id) as present_today
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.is_active = TRUE
            LEFT JOIN attendance a ON s.id = a.student_id AND a.attendance_date = %s
            WHERE c.is_active = TRUE
            GROUP BY c.id, c.class_name, c.section
            ORDER BY c.class_name, c.section
        """
        class_attendance = db.execute_query(query, (today,)) or []
        
        return render_template('principal/dashboard.html', 
                             stats=stats, 
                             recent_sessions=recent_sessions,
                             class_attendance=class_attendance)
        
    except Exception as e:
        logging.error(f"Error loading principal dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('principal/dashboard.html', 
                             stats={}, 
                             recent_sessions=[],
                             class_attendance=[])

@principal_bp.route('/students')
@login_required
def manage_students():
    """Manage students"""
    try:
        # Get all students with class information
        students = StudentModel.get_all_students()
        
        # Get all classes for the dropdown
        query = "SELECT * FROM classes WHERE is_active = TRUE ORDER BY class_name, section"
        classes = db.execute_query(query) or []
        
        return render_template('principal/students.html', 
                             students=students, 
                             classes=classes)
        
    except Exception as e:
        logging.error(f"Error loading students: {e}")
        flash('Error loading students', 'error')
        return render_template('principal/students.html', students=[], classes=[])

@principal_bp.route('/enroll-student', methods=['GET', 'POST'])
@login_required
def enroll_student():
    """Enroll new student"""
    if request.method == 'POST':
        try:
            # Extract form data
            student_data = {
                'student_id': request.form['student_id'],
                'full_name': request.form['full_name'],
                'class_id': int(request.form['class_id']),
                'roll_number': request.form['roll_number'],
                'father_name': request.form.get('father_name', ''),
                'mother_name': request.form.get('mother_name', ''),
                'date_of_birth': request.form.get('date_of_birth'),
                'address': request.form.get('address', ''),
                'phone': request.form.get('phone', ''),
                'enrollment_date': request.form.get('enrollment_date', date.today()),
                'consent_given': 'consent_given' in request.form
            }
            
            # Validate required fields
            required_fields = ['student_id', 'full_name', 'class_id', 'roll_number']
            for field in required_fields:
                if not student_data[field]:
                    flash(f'{field.replace("_", " ").title()} is required', 'error')
                    return redirect(url_for('principal.enroll_student'))
            
            # Check if student ID already exists
            if StudentModel.check_student_id_exists(student_data['student_id']):
                flash('Student ID already exists', 'error')
                return redirect(url_for('principal.enroll_student'))
            
            # Check if roll number already exists in class
            if StudentModel.check_roll_number_exists(student_data['roll_number'], student_data['class_id']):
                flash('Roll number already exists in this class', 'error')
                return redirect(url_for('principal.enroll_student'))
            
            # Handle file upload
            photo_filename = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename != '':
                    from config import Config
                    if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        filename = secure_filename(f"{student_data['student_id']}_{file.filename}")
                        filepath = os.path.join(Config.STUDENT_PHOTOS_PATH, filename)
                        file.save(filepath)
                        photo_filename = filename
                        
                        # Process face encoding
                        success, message = face_manager.add_student_face(
                            filepath, student_data['student_id'], student_data['full_name']
                        )
                        
                        if not success:
                            flash(f"Face processing warning: {message}", 'warning')
            
            # Get class information for QR code
            class_query = "SELECT class_name, section FROM classes WHERE id = %s"
            class_result = db.execute_query(class_query, (student_data['class_id'],))
            if class_result:
                student_data.update(class_result[0])
            
            # Generate QR code
            qr_success, qr_filename, qr_data = qr_manager.generate_student_qr(student_data)
            if not qr_success:
                flash("QR code generation failed", 'warning')
            
            # Add photo filename and QR data to student data
            student_data['photo_filename'] = photo_filename
            student_data['qr_code'] = qr_data
            
            # Create student
            success, message, student_id = StudentModel.create_student(student_data)
            
            if success:
                flash('Student enrolled successfully!', 'success')
                return redirect(url_for('principal.manage_students'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            logging.error(f"Error enrolling student: {e}")
            flash('An error occurred while enrolling the student.', 'error')
    
    # GET request - show enrollment form
    query = "SELECT * FROM classes WHERE is_active = TRUE ORDER BY class_name, section"
    classes = db.execute_query(query) or []
    
    return render_template('principal/enroll_student.html', classes=classes)

@principal_bp.route('/teachers')
@login_required
def manage_teachers():
    """Manage teachers"""
    try:
        teachers = UserModel.get_teachers()
        return render_template('principal/teachers.html', teachers=teachers)
        
    except Exception as e:
        logging.error(f"Error loading teachers: {e}")
        flash('Error loading teachers', 'error')
        return render_template('principal/teachers.html', teachers=[])

@principal_bp.route('/reports')
@login_required
def reports():
    """Generate reports"""
    try:
        # Get all classes for report selection
        query = "SELECT * FROM classes WHERE is_active = TRUE ORDER BY class_name, section"
        classes = db.execute_query(query) or []
        
        return render_template('principal/reports.html', classes=classes)
        
    except Exception as e:
        logging.error(f"Error loading reports: {e}")
        flash('Error loading reports', 'error')
        return render_template('principal/reports.html', classes=[])

@principal_bp.route('/reports/attendance', methods=['POST'])
@login_required
def generate_attendance_report():
    """Generate attendance report"""
    try:
        class_id = request.form.get('class_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not all([class_id, start_date, end_date]):
            flash('Please select class and date range', 'error')
            return redirect(url_for('principal.reports'))
        
        # Get attendance summary
        summary = AttendanceModel.get_attendance_summary(int(class_id), start_date, end_date)
        
        # Get class information
        class_query = "SELECT * FROM classes WHERE id = %s"
        class_result = db.execute_query(class_query, (class_id,))
        class_info = class_result[0] if class_result else {}
        
        return render_template('principal/attendance_report.html',
                             summary=summary,
                             class_info=class_info,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logging.error(f"Error generating attendance report: {e}")
        flash('Error generating report', 'error')
        return redirect(url_for('principal.reports'))

@principal_bp.route('/bulk-enrollment', methods=['GET', 'POST'])
@login_required
def bulk_enrollment():
    """Bulk enrollment using OCR"""
    if request.method == 'POST':
        try:
            if 'forms' not in request.files:
                flash('No files selected', 'error')
                return redirect(url_for('principal.bulk_enrollment'))
            
            files = request.files.getlist('forms')
            if not files or files[0].filename == '':
                flash('No files selected', 'error')
                return redirect(url_for('principal.bulk_enrollment'))
            
            # Process each form
            results = []
            for file in files:
                if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Save temporary file
                    from config import Config
                    filename = secure_filename(file.filename)
                    temp_path = os.path.join(Config.UPLOAD_FOLDER, 'temp', filename)
                    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                    file.save(temp_path)
                    
                    # Process OCR
                    form_data, error = ocr_processor.extract_form_data(temp_path)
                    
                    # Clean up temporary file
                    os.remove(temp_path)
                    
                    results.append({
                        'filename': filename,
                        'success': error is None,
                        'error': error,
                        'data': form_data
                    })
            
            return render_template('principal/bulk_enrollment_results.html', results=results)
            
        except Exception as e:
            logging.error(f"Error in bulk enrollment: {e}")
            flash('Error processing forms', 'error')
    
    return render_template('principal/bulk_enrollment.html')

@principal_bp.route('/settings')
@login_required
def settings():
    """System settings"""
    return render_template('principal/settings.html')

@principal_bp.route('/api/class-stats/<int:class_id>')
@login_required
def get_class_stats(class_id):
    """Get statistics for a specific class"""
    try:
        stats = AttendanceModel.get_class_attendance_stats(class_id)
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        logging.error(f"Error getting class stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500

@principal_bp.route('/api/student/<student_id>', methods=['DELETE'])
@login_required
def delete_student_api(student_id):
    """Delete student via API"""
    try:
        success, message = StudentModel.delete_student(student_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        logging.error(f"Error deleting student: {e}")
        return jsonify({'success': False, 'error': 'Failed to delete student'}), 500
