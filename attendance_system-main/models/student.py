"""
Student Model - Handles student-related database operations
"""

from utils.database import db
from datetime import date
import logging

class StudentModel:
    """Model class for student operations"""
    
    @staticmethod
    def create_student(student_data):
        """Create a new student record"""
        try:
            query = """
                INSERT INTO students 
                (student_id, full_name, class_id, roll_number, father_name, mother_name,
                 date_of_birth, address, phone, photo_filename, qr_code, enrollment_date, consent_given)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                student_data['student_id'],
                student_data['full_name'],
                student_data['class_id'],
                student_data['roll_number'],
                student_data.get('father_name', ''),
                student_data.get('mother_name', ''),
                student_data.get('date_of_birth'),
                student_data.get('address', ''),
                student_data.get('phone', ''),
                student_data.get('photo_filename'),
                student_data.get('qr_code'),
                student_data.get('enrollment_date', date.today()),
                student_data.get('consent_given', False)
            )
            
            result = db.execute_query(query, params)
            
            if result and result['affected_rows'] > 0:
                return True, "Student created successfully", result['last_id']
            else:
                return False, "Failed to create student", None
                
        except Exception as e:
            logging.error(f"Error creating student: {e}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def get_student_by_id(student_id):
        """Get student by student_id"""
        try:
            query = """
                SELECT s.*, c.class_name, c.section
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.student_id = %s AND s.is_active = TRUE
            """
            result = db.execute_query(query, (student_id,))
            return result[0] if result else None
            
        except Exception as e:
            logging.error(f"Error getting student by ID: {e}")
            return None
    
    @staticmethod
    def get_students_by_class(class_id):
        """Get all students in a specific class"""
        try:
            query = """
                SELECT s.*, c.class_name, c.section
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.class_id = %s AND s.is_active = TRUE
                ORDER BY s.roll_number
            """
            result = db.execute_query(query, (class_id,))
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting students by class: {e}")
            return []
    
    @staticmethod
    def get_all_students():
        """Get all active students"""
        try:
            query = """
                SELECT s.*, c.class_name, c.section
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.is_active = TRUE
                ORDER BY c.class_name, c.section, s.roll_number
            """
            result = db.execute_query(query)
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting all students: {e}")
            return []
    
    @staticmethod
    def update_student(student_id, update_data):
        """Update student information"""
        try:
            # Build dynamic query based on provided fields
            fields = []
            values = []
            
            for key, value in update_data.items():
                if key in ['full_name', 'father_name', 'mother_name', 'date_of_birth', 
                          'address', 'phone', 'photo_filename', 'qr_code', 'consent_given']:
                    fields.append(f"{key} = %s")
                    values.append(value)
            
            if not fields:
                return False, "No valid fields to update"
            
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(student_id)
            
            query = f"UPDATE students SET {', '.join(fields)} WHERE student_id = %s"
            result = db.execute_query(query, values)
            
            if result and result['affected_rows'] > 0:
                return True, "Student updated successfully"
            else:
                return False, "Failed to update student"
                
        except Exception as e:
            logging.error(f"Error updating student: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def delete_student(student_id):
        """Soft delete a student (mark as inactive)"""
        try:
            query = """
                UPDATE students 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
            """
            result = db.execute_query(query, (student_id,))
            
            if result and result['affected_rows'] > 0:
                return True, "Student deleted successfully"
            else:
                return False, "Failed to delete student"
                
        except Exception as e:
            logging.error(f"Error deleting student: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def search_students(search_term):
        """Search students by name, student_id, or roll_number"""
        try:
            query = """
                SELECT s.*, c.class_name, c.section
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.is_active = TRUE AND (
                    s.full_name LIKE %s OR 
                    s.student_id LIKE %s OR 
                    s.roll_number LIKE %s
                )
                ORDER BY c.class_name, c.section, s.roll_number
            """
            search_pattern = f"%{search_term}%"
            result = db.execute_query(query, (search_pattern, search_pattern, search_pattern))
            return result or []
            
        except Exception as e:
            logging.error(f"Error searching students: {e}")
            return []
    
    @staticmethod
    def get_student_attendance_summary(student_id, start_date=None, end_date=None):
        """Get attendance summary for a student"""
        try:
            if not start_date:
                start_date = date.today().replace(day=1)  # First day of current month
            if not end_date:
                end_date = date.today()
            
            query = """
                SELECT 
                    COUNT(a.id) as total_days,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_days,
                    ROUND(
                        (SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.id)), 2
                    ) as attendance_percentage
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id 
                    AND a.attendance_date BETWEEN %s AND %s
                WHERE s.student_id = %s AND s.is_active = TRUE
            """
            result = db.execute_query(query, (start_date, end_date, student_id))
            return result[0] if result else {}
            
        except Exception as e:
            logging.error(f"Error getting student attendance summary: {e}")
            return {}
    
    @staticmethod
    def check_roll_number_exists(roll_number, class_id, exclude_student_id=None):
        """Check if roll number already exists in the class"""
        try:
            query = """
                SELECT id FROM students 
                WHERE roll_number = %s AND class_id = %s AND is_active = TRUE
            """
            params = [roll_number, class_id]
            
            if exclude_student_id:
                query += " AND student_id != %s"
                params.append(exclude_student_id)
            
            result = db.execute_query(query, params)
            return len(result) > 0 if result else False
            
        except Exception as e:
            logging.error(f"Error checking roll number: {e}")
            return False
    
    @staticmethod
    def check_student_id_exists(student_id, exclude_student_id=None):
        """Check if student_id already exists"""
        try:
            query = "SELECT id FROM students WHERE student_id = %s AND is_active = TRUE"
            params = [student_id]
            
            if exclude_student_id:
                query += " AND student_id != %s"
                params.append(exclude_student_id)
            
            result = db.execute_query(query, params)
            return len(result) > 0 if result else False
            
        except Exception as e:
            logging.error(f"Error checking student ID: {e}")
            return False
    
    @staticmethod
    def get_student_statistics():
        """Get overall student statistics"""
        try:
            # Total students
            total_query = "SELECT COUNT(*) as count FROM students WHERE is_active = TRUE"
            total_result = db.execute_query(total_query)
            total_students = total_result[0]['count'] if total_result else 0
            
            # Students by class
            class_query = """
                SELECT c.class_name, c.section, COUNT(s.id) as student_count
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id AND s.is_active = TRUE
                WHERE c.is_active = TRUE
                GROUP BY c.id, c.class_name, c.section
                ORDER BY c.class_name, c.section
            """
            class_stats = db.execute_query(class_query) or []
            
            # Recent enrollments
            recent_query = """
                SELECT s.*, c.class_name, c.section
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.is_active = TRUE
                ORDER BY s.created_at DESC
                LIMIT 10
            """
            recent_enrollments = db.execute_query(recent_query) or []
            
            return {
                'total_students': total_students,
                'class_statistics': class_stats,
                'recent_enrollments': recent_enrollments
            }
            
        except Exception as e:
            logging.error(f"Error getting student statistics: {e}")
            return {'total_students': 0, 'class_statistics': [], 'recent_enrollments': []}
