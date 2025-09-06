"""
User Model - Handles user (teacher/principal) related database operations
"""

from utils.database import db
from werkzeug.security import generate_password_hash, check_password_hash
import logging

class UserModel:
    """Model class for user operations"""
    
    @staticmethod
    def create_user(user_data):
        """Create a new user (teacher or principal)"""
        try:
            # Hash the password
            password_hash = generate_password_hash(user_data['password'])
            
            query = """
                INSERT INTO users 
                (username, password_hash, full_name, email, role)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                user_data['username'],
                password_hash,
                user_data['full_name'],
                user_data['email'],
                user_data['role']
            )
            
            result = db.execute_query(query, params)
            
            if result and result['affected_rows'] > 0:
                return True, "User created successfully", result['last_id']
            else:
                return False, "Failed to create user", None
                
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate user login"""
        try:
            query = """
                SELECT * FROM users 
                WHERE username = %s AND is_active = TRUE
            """
            result = db.execute_query(query, (username,))
            
            if result and len(result) > 0:
                user = result[0]
                if check_password_hash(user['password_hash'], password):
                    return True, user
                else:
                    return False, "Invalid password"
            else:
                return False, "User not found or inactive"
                
        except Exception as e:
            logging.error(f"Error authenticating user: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        try:
            query = """
                SELECT * FROM users 
                WHERE id = %s AND is_active = TRUE
            """
            result = db.execute_query(query, (user_id,))
            return result[0] if result else None
            
        except Exception as e:
            logging.error(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        try:
            query = """
                SELECT * FROM users 
                WHERE username = %s AND is_active = TRUE
            """
            result = db.execute_query(query, (username,))
            return result[0] if result else None
            
        except Exception as e:
            logging.error(f"Error getting user by username: {e}")
            return None
    
    @staticmethod
    def get_all_users():
        """Get all active users"""
        try:
            query = """
                SELECT id, username, full_name, email, role, created_at
                FROM users 
                WHERE is_active = TRUE
                ORDER BY role, full_name
            """
            result = db.execute_query(query)
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return []
    
    @staticmethod
    def get_teachers():
        """Get all active teachers"""
        try:
            query = """
                SELECT u.*, COUNT(c.id) as class_count
                FROM users u
                LEFT JOIN classes c ON u.id = c.teacher_id AND c.is_active = TRUE
                WHERE u.role = 'teacher' AND u.is_active = TRUE
                GROUP BY u.id
                ORDER BY u.full_name
            """
            result = db.execute_query(query)
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting teachers: {e}")
            return []
    
    @staticmethod
    def update_user(user_id, update_data):
        """Update user information"""
        try:
            # Build dynamic query based on provided fields
            fields = []
            values = []
            
            for key, value in update_data.items():
                if key in ['full_name', 'email', 'role']:
                    fields.append(f"{key} = %s")
                    values.append(value)
                elif key == 'password':
                    # Hash the new password
                    fields.append("password_hash = %s")
                    values.append(generate_password_hash(value))
            
            if not fields:
                return False, "No valid fields to update"
            
            fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            result = db.execute_query(query, values)
            
            if result and result['affected_rows'] > 0:
                return True, "User updated successfully"
            else:
                return False, "Failed to update user"
                
        except Exception as e:
            logging.error(f"Error updating user: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def delete_user(user_id):
        """Soft delete a user (mark as inactive)"""
        try:
            query = """
                UPDATE users 
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            result = db.execute_query(query, (user_id,))
            
            if result and result['affected_rows'] > 0:
                return True, "User deleted successfully"
            else:
                return False, "Failed to delete user"
                
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """Change user password"""
        try:
            # First verify the old password
            user = UserModel.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            if not check_password_hash(user['password_hash'], old_password):
                return False, "Current password is incorrect"
            
            # Update with new password
            new_password_hash = generate_password_hash(new_password)
            query = """
                UPDATE users 
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            result = db.execute_query(query, (new_password_hash, user_id))
            
            if result and result['affected_rows'] > 0:
                return True, "Password changed successfully"
            else:
                return False, "Failed to change password"
                
        except Exception as e:
            logging.error(f"Error changing password: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def check_username_exists(username, exclude_user_id=None):
        """Check if username already exists"""
        try:
            query = "SELECT id FROM users WHERE username = %s AND is_active = TRUE"
            params = [username]
            
            if exclude_user_id:
                query += " AND id != %s"
                params.append(exclude_user_id)
            
            result = db.execute_query(query, params)
            return len(result) > 0 if result else False
            
        except Exception as e:
            logging.error(f"Error checking username: {e}")
            return False
    
    @staticmethod
    def check_email_exists(email, exclude_user_id=None):
        """Check if email already exists"""
        try:
            query = "SELECT id FROM users WHERE email = %s AND is_active = TRUE"
            params = [email]
            
            if exclude_user_id:
                query += " AND id != %s"
                params.append(exclude_user_id)
            
            result = db.execute_query(query, params)
            return len(result) > 0 if result else False
            
        except Exception as e:
            logging.error(f"Error checking email: {e}")
            return False
    
    @staticmethod
    def get_user_statistics():
        """Get user statistics"""
        try:
            # Total users by role
            role_query = """
                SELECT role, COUNT(*) as count
                FROM users 
                WHERE is_active = TRUE
                GROUP BY role
            """
            role_stats = db.execute_query(role_query) or []
            
            # Recent users
            recent_query = """
                SELECT id, username, full_name, role, created_at
                FROM users 
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 10
            """
            recent_users = db.execute_query(recent_query) or []
            
            return {
                'role_statistics': role_stats,
                'recent_users': recent_users
            }
            
        except Exception as e:
            logging.error(f"Error getting user statistics: {e}")
            return {'role_statistics': [], 'recent_users': []}
    
    @staticmethod
    def assign_teacher_to_class(teacher_id, class_id):
        """Assign a teacher to a class"""
        try:
            query = """
                UPDATE classes 
                SET teacher_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            result = db.execute_query(query, (teacher_id, class_id))
            
            if result and result['affected_rows'] > 0:
                return True, "Teacher assigned to class successfully"
            else:
                return False, "Failed to assign teacher to class"
                
        except Exception as e:
            logging.error(f"Error assigning teacher to class: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_teacher_classes(teacher_id):
        """Get all classes assigned to a teacher"""
        try:
            query = """
                SELECT c.*, COUNT(s.id) as student_count
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id AND s.is_active = TRUE
                WHERE c.teacher_id = %s AND c.is_active = TRUE
                GROUP BY c.id
                ORDER BY c.class_name, c.section
            """
            result = db.execute_query(query, (teacher_id,))
            return result or []
            
        except Exception as e:
            logging.error(f"Error getting teacher classes: {e}")
            return []
