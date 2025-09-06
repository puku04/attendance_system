"""
Teacher Routes - Handles teacher-specific functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.student import StudentModel
from models.attendance import AttendanceModel
from models.user import UserModel
from utils.face_recognition import face_manager
from utils.qr_code import qr_manager
from utils.database import db
from datetime import date, datetime
import logging
import os
from werkzeug.utils import secure_filename

# Create teacher blueprint
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'teacher':
            flash('Access denied. Teacher access required.', 'error')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/dashboard')
@login_required
def dashboard():
    """Teacher dashboard"""
    try:
        teacher_id = session['user_id']
        
        # Get teacher's classes
        query = """
            SELECT c.*, COUNT(s.id) as student_count
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id AND s.is_active = TRUE
            WHERE c.teacher_id = %s AND c.is_active = TRUE
            GROUP BY c.id
            ORDER BY c.class_name, c.section
        """
        classes = db.execute_query(query, (teacher_id,)) or []
        
        # Today's attendance summary
        today = date.today()
        attendance_summary = []
        
        for class_info in classes:
            query = """
                SELECT COUNT(*) as present_count
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.attendance_date = %s AND s.class_id = %s AND a.status = 'present'
            """
            result = db.execute_query(query, (today, class_info['id']))
            present_count = result[0]['present_count'] if result else 0
            
            attendance_summary.append({
                'class_info': class_info,
                'present_today': present_count,
                'total_students': class_info['student_count']
            })
        
        # Recent attendance sessions
        query = """
            SELECT s.*, c.class_name, c.section
            FROM attendance_sessions s
            JOIN classes c ON s.class_id = c.id
            WHERE s.teacher_id = %s
            ORDER BY s.created_at DESC
            LIMIT 5
        """
        recent_sessions = db.execute_query(query, (teacher_id,)) or []
        
        return render_template('teacher/dashboard.html', 
                             classes=classes,
                             attendance_summary=attendance_summary,
                             recent_sessions=recent_sessions)
        
    except Exception as e:
        logging.error(f"Error loading teacher dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('teacher/dashboard.html', 
                             classes=[],
                             attendance_summary=[],
                             recent_sessions=[])

@teacher_bp.route('/take-attendance/<int:class_id>')
@login_required
def take_attendance(class_id):
    """Take attendance for a class"""
    try:
        teacher_id = session['user_id']
        
        # Verify teacher has access to this class
        query = "SELECT * FROM classes WHERE id = %s AND teacher_id = %s"
        class_result = db.execute_query(query, (class_id, teacher_id))
        
        if not class_result:
            flash('Access denied to this class.', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        class_info = class_result[0]
        
        # Get students in this class
        students = StudentModel.get_students_by_class(class_id)
        
        # Check if attendance already taken today
        today = date.today()
        query = """
            SELECT COUNT(*) as count 
            FROM attendance a 
            JOIN students s ON a.student_id = s.id 
            WHERE s.class_id = %s AND a.attendance_date = %s
        """
        attendance_taken = db.execute_query(query, (class_id, today))
        already_taken = attendance_taken[0]['count'] > 0 if attendance_taken else False
        
        return render_template('teacher/take_attendance.html',
                             class_info=class_info,
                             students=students,
                             already_taken=already_taken)
        
    except Exception as e:
        logging.error(f"Error loading take attendance page: {e}")
        flash('Error loading attendance page', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/process-attendance', methods=['POST'])
@login_required
def process_attendance():
    """Process attendance using face recognition"""
    try:
        class_id = int(request.form['class_id'])
        teacher_id = session['user_id']
        
        # Verify teacher access
        query = "SELECT * FROM classes WHERE id = %s AND teacher_id = %s"
        class_result = db.execute_query(query, (class_id, teacher_id))
        if not class_result:
            return jsonify({'success': False, 'error': 'Access denied'})
        
        # Handle file upload
        if 'attendance_photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo uploaded'})
        
        file = request.files['attendance_photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'})
        
        # Save uploaded photo
        from config import Config
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"attendance_{class_id}_{timestamp}_{file.filename}")
        filepath = os.path.join(Config.ATTENDANCE_PHOTOS_PATH, filename)
        file.save(filepath)
        
        # Process face recognition
        recognition_result = face_manager.recognize_faces_in_image(filepath)
        
        if not recognition_result['success']:
            return jsonify({
                'success': False,
                'error': f"Face recognition failed: {recognition_result['error']}"
            })
        
        # Create attendance session
        session_query = """
            INSERT INTO attendance_sessions 
            (class_id, teacher_id, session_date, photo_filename, 
             total_students_detected, total_students_recognized, processing_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'completed')
        """
        
        session_params = (
            class_id, teacher_id, date.today(), filename,
            recognition_result['total_faces_detected'],
            len(recognition_result['recognized_students'])
        )
        
        session_result = db.execute_query(session_query, session_params)
        session_id = session_result['last_id']
        
        # Mark attendance for recognized students
        today = date.today()
        attendance_records = []
        
        for student in recognition_result['recognized_students']:
            # Check if attendance already exists for today
            check_query = """
                SELECT id FROM attendance 
                WHERE student_id = (SELECT id FROM students WHERE student_id = %s) 
                AND attendance_date = %s
            """
            existing = db.execute_query(check_query, (student['student_id'], today))
            
            if not existing:
                attendance_query = """
                    INSERT INTO attendance 
                    (student_id, class_id, teacher_id, attendance_date, 
                     status, method, confidence_score, photo_filename)
                    VALUES 
                    ((SELECT id FROM students WHERE student_id = %s), %s, %s, %s, 
                     'present', 'face_recognition', %s, %s)
                """
                
                attendance_params = (
                    student['student_id'], class_id, teacher_id, today,
                    student['confidence'], filename
                )
                
                db.execute_query(attendance_query, attendance_params)
                attendance_records.append(student)
        
        # Get list of all students for absent marking
        all_students_query = """
            SELECT student_id, full_name FROM students 
            WHERE class_id = %s AND is_active = TRUE
        """
        all_students = db.execute_query(all_students_query, (class_id,)) or []
        
        recognized_ids = [s['student_id'] for s in recognition_result['recognized_students']]
        absent_students = [s for s in all_students if s['student_id'] not in recognized_ids]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'total_faces_detected': recognition_result['total_faces_detected'],
            'recognized_students': recognition_result['recognized_students'],
            'attendance_marked': len(attendance_records),
            'absent_students': absent_students,
            'unrecognized_faces': recognition_result['unrecognized_faces']
        })
        
    except Exception as e:
        logging.error(f"Error processing attendance: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'})

@teacher_bp.route('/qr-scanner/<int:class_id>')
@login_required
def qr_scanner(class_id):
    """QR code scanner for attendance"""
    try:
        teacher_id = session['user_id']
        
        # Verify teacher access to class
        query = "SELECT * FROM classes WHERE id = %s AND teacher_id = %s"
        class_result = db.execute_query(query, (class_id, teacher_id))
        
        if not class_result:
            flash('Access denied to this class.', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        class_info = class_result[0]
        
        return render_template('teacher/qr_scanner.html', 
                             class_info=class_info)
        
    except Exception as e:
        logging.error(f"Error loading QR scanner: {e}")
        flash('Error loading QR scanner', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/scan-qr', methods=['POST'])
@login_required
def scan_qr():
    """Process QR code scan for attendance"""
    try:
        qr_data = request.json.get('qr_data')
        class_id = request.json.get('class_id')
        
        if not qr_data or not class_id:
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        # Decode QR data
        success, decoded_data = qr_manager.decode_qr_data(qr_data)
        if not success:
            return jsonify({'success': False, 'error': decoded_data})
        
        student_id = decoded_data['student_id']
        
        # Verify student exists and belongs to this class
        query = """
            SELECT s.*, c.class_name, c.section 
            FROM students s 
            JOIN classes c ON s.class_id = c.id 
            WHERE s.student_id = %s AND s.class_id = %s AND s.is_active = TRUE
        """
        student_result = db.execute_query(query, (student_id, class_id))
        
        if not student_result:
            return jsonify({'success': False, 'error': 'Student not found in this class'})
        
        student = student_result[0]
        
        # Check if attendance already marked today
        today = date.today()
        check_query = """
            SELECT id FROM attendance 
            WHERE student_id = %s AND attendance_date = %s
        """
        existing = db.execute_query(check_query, (student['id'], today))
        
        if existing:
            return jsonify({
                'success': False, 
                'error': 'Attendance already marked for this student today'
            })
        
        # Mark attendance
        attendance_query = """
            INSERT INTO attendance 
            (student_id, class_id, teacher_id, attendance_date, 
             status, method, photo_filename, notes)
            VALUES (%s, %s, %s, %s, 'present', 'qr_code', NULL, 'QR code scan')
        """
        
        attendance_params = (
            student['id'], class_id, session['user_id'], today
        )
        
        result = db.execute_query(attendance_query, attendance_params)
        
        if result and result['affected_rows'] > 0:
            return jsonify({
                'success': True,
                'student': {
                    'name': student['full_name'],
                    'student_id': student['student_id'],
                    'roll_number': student['roll_number']
                },
                'message': 'Attendance marked successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to mark attendance'})
            
    except Exception as e:
        logging.error(f"Error processing QR scan: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'})

@teacher_bp.route('/class-list/<int:class_id>')
@login_required
def class_list(class_id):
    """View class list"""
    try:
        teacher_id = session['user_id']
        
        # Verify teacher access to class
        query = "SELECT * FROM classes WHERE id = %s AND teacher_id = %s"
        class_result = db.execute_query(query, (class_id, teacher_id))
        
        if not class_result:
            flash('Access denied to this class.', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        class_info = class_result[0]
        students = StudentModel.get_students_by_class(class_id)
        
        return render_template('teacher/class_list.html',
                             class_info=class_info,
                             students=students)
        
    except Exception as e:
        logging.error(f"Error loading class list: {e}")
        flash('Error loading class list', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/attendance-history/<int:class_id>')
@login_required
def attendance_history(class_id):
    """View attendance history for a class"""
    try:
        teacher_id = session['user_id']
        
        # Verify teacher access to class
        query = "SELECT * FROM classes WHERE id = %s AND teacher_id = %s"
        class_result = db.execute_query(query, (class_id, teacher_id))
        
        if not class_result:
            flash('Access denied to this class.', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        class_info = class_result[0]
        
        # Get date range from request
        start_date = request.args.get('start_date', date.today().replace(day=1).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', date.today().strftime('%Y-%m-%d'))
        
        # Get attendance summary
        summary = AttendanceModel.get_attendance_summary(class_id, start_date, end_date)
        
        return render_template('teacher/attendance_history.html',
                             class_info=class_info,
                             summary=summary,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        logging.error(f"Error loading attendance history: {e}")
        flash('Error loading attendance history', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/api/attendance-summary/<int:class_id>')
@login_required
def attendance_summary_api(class_id):
    """Get attendance summary via API"""
    try:
        today = date.today()
        
        # Get present students
        present_query = """
            SELECT s.full_name, s.student_id, s.roll_number, 
                   a.time_marked, a.method, a.confidence_score
            FROM students s
            JOIN attendance a ON s.id = a.student_id
            WHERE s.class_id = %s AND a.attendance_date = %s AND a.status = 'present'
            ORDER BY s.roll_number
        """
        present_students = db.execute_query(present_query, (class_id, today)) or []
        
        # Get absent students
        absent_query = """
            SELECT s.full_name, s.student_id, s.roll_number
            FROM students s
            WHERE s.class_id = %s AND s.is_active = TRUE
            AND s.id NOT IN (
                SELECT student_id FROM attendance 
                WHERE attendance_date = %s AND status = 'present'
            )
            ORDER BY s.roll_number
        """
        absent_students = db.execute_query(absent_query, (class_id, today)) or []
        
        return jsonify({
            'success': True,
            'date': today.strftime('%Y-%m-%d'),
            'present_students': present_students,
            'absent_students': absent_students,
            'total_present': len(present_students),
            'total_absent': len(absent_students)
        })
        
    except Exception as e:
        logging.error(f"Error getting attendance summary: {e}")
        return jsonify({'success': False, 'error': 'Failed to get attendance summary'}), 500
