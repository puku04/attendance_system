"""
Attendance Model - Handles attendance-related database operations
"""

from utils.database import db
from datetime import date, datetime
import logging

class AttendanceModel:
    """Model class for attendance operations"""
    
    @staticmethod
    def mark_attendance(student_id, class_id, teacher_id, status='present', method='manual', 
                       confidence_score=None, photo_filename=None, notes=None):
        """Mark attendance for a student"""
        try:
            today = date.today()
            
            # Check if attendance already exists for today
            check_query = """
                SELECT id FROM attendance 
                WHERE student_id = %s AND attendance_date = %s
            """
            existing = db.execute_query(check_query, (student_id, today))
            
            if existing:
                return False, "Attendance already marked for this student today"
            
            # Insert attendance record
            insert_query = """
                INSERT INTO attendance 
                (student_id, class_id, teacher_id, attendance_date, 
                 status, method, confidence_score, photo_filename, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                student_id, class_id, teacher_id, today,
                status, method, confidence_score, photo_filename, notes
            )
            
            result = db.execute_query(insert_query, params)
            
            if result and result['affected_rows'] > 0:
                return True, "Attendance marked successfully"
            else:
                return False, "Failed to mark attendance"
                
        except Exception as e:
            logging.error(f"Error marking attendance: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_attendance_by_date(class_id, attendance_date):
        """Get attendance records for a specific class and date"""
        try:
            query = """
                SELECT a.*, s.full_name, s.student_id, s.roll_number
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.class_id = %s AND a.attendance_date = %s
                ORDER BY s.roll_number
            """
            result = db.execute_query(query, (class_id, attendance_date))
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting attendance by date: {e}")
            return []
    
    @staticmethod
    def get_attendance_summary(class_id, start_date, end_date):
        """Get attendance summary for a class within date range"""
        try:
            query = """
                SELECT 
                    s.student_id,
                    s.full_name,
                    s.roll_number,
                    COUNT(a.id) as total_days,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_days,
                    ROUND(
                        (SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.id)), 2
                    ) as attendance_percentage
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id 
                    AND a.attendance_date BETWEEN %s AND %s
                WHERE s.class_id = %s AND s.is_active = TRUE
                GROUP BY s.id, s.student_id, s.full_name, s.roll_number
                ORDER BY s.roll_number
            """
            result = db.execute_query(query, (start_date, end_date, class_id))
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting attendance summary: {e}")
            return []
    
    @staticmethod
    def get_student_attendance_history(student_id, start_date=None, end_date=None):
        """Get attendance history for a specific student"""
        try:
            if not start_date:
                start_date = date.today().replace(day=1)  # First day of current month
            if not end_date:
                end_date = date.today()
            
            query = """
                SELECT a.*, c.class_name, c.section, u.full_name as teacher_name
                FROM attendance a
                JOIN classes c ON a.class_id = c.id
                JOIN users u ON a.teacher_id = u.id
                WHERE a.student_id = %s AND a.attendance_date BETWEEN %s AND %s
                ORDER BY a.attendance_date DESC, a.time_marked DESC
            """
            result = db.execute_query(query, (student_id, start_date, end_date))
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting student attendance history: {e}")
            return []
    
    @staticmethod
    def update_attendance(attendance_id, status, notes=None):
        """Update an existing attendance record"""
        try:
            query = """
                UPDATE attendance 
                SET status = %s, notes = %s, time_marked = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            result = db.execute_query(query, (status, notes, attendance_id))
            
            if result and result['affected_rows'] > 0:
                return True, "Attendance updated successfully"
            else:
                return False, "Failed to update attendance"
                
        except Exception as e:
            logging.error(f"Error updating attendance: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def delete_attendance(attendance_id):
        """Delete an attendance record"""
        try:
            query = "DELETE FROM attendance WHERE id = %s"
            result = db.execute_query(query, (attendance_id,))
            
            if result and result['affected_rows'] > 0:
                return True, "Attendance deleted successfully"
            else:
                return False, "Failed to delete attendance"
                
        except Exception as e:
            logging.error(f"Error deleting attendance: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_class_attendance_stats(class_id, date_range_days=30):
        """Get attendance statistics for a class"""
        try:
            end_date = date.today()
            start_date = date.fromordinal(end_date.toordinal() - date_range_days)
            
            # Daily attendance stats
            daily_query = """
                SELECT 
                    a.attendance_date,
                    COUNT(DISTINCT s.id) as total_students,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
                    ROUND(
                        (SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT s.id)), 2
                    ) as attendance_percentage
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.attendance_date BETWEEN %s AND %s
                WHERE s.class_id = %s AND s.is_active = TRUE
                GROUP BY a.attendance_date
                ORDER BY a.attendance_date DESC
            """
            daily_stats = db.execute_query(daily_query, (start_date, end_date, class_id)) or []
            
            # Overall stats
            overall_query = """
                SELECT 
                    COUNT(DISTINCT s.id) as total_students,
                    COUNT(DISTINCT a.attendance_date) as total_days,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as total_present,
                    ROUND(
                        (SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100.0 / 
                         (COUNT(DISTINCT s.id) * COUNT(DISTINCT a.attendance_date))), 2
                    ) as overall_percentage
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.attendance_date BETWEEN %s AND %s
                WHERE s.class_id = %s AND s.is_active = TRUE
            """
            overall_stats = db.execute_query(overall_query, (start_date, end_date, class_id))
            
            return {
                'daily_stats': daily_stats,
                'overall_stats': overall_stats[0] if overall_stats else {},
                'date_range': {'start': start_date, 'end': end_date}
            }
            
        except Exception as e:
            logging.error(f"Error getting class attendance stats: {e}")
            return {'daily_stats': [], 'overall_stats': {}, 'date_range': {}}
