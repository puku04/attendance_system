"""
Authentication Routes - Handles user authentication and authorization
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import UserModel
import logging

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    """Decorator to require specific role"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Authenticate user
        success, result = UserModel.authenticate_user(username, password)
        
        if success:
            user = result
            # Set session variables
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['email'] = user['email']
            
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user['role'] == 'principal':
                return redirect(url_for('principal.dashboard'))
            else:
                return redirect(url_for('teacher.dashboard'))
        else:
            flash(result, 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@role_required('principal')
def register():
    """Register new user (principal only)"""
    if request.method == 'POST':
        try:
            # Get form data
            user_data = {
                'username': request.form['username'],
                'password': request.form['password'],
                'full_name': request.form['full_name'],
                'email': request.form['email'],
                'role': request.form['role']
            }
            
            # Validate required fields
            required_fields = ['username', 'password', 'full_name', 'email', 'role']
            for field in required_fields:
                if not user_data[field]:
                    flash(f'{field.replace("_", " ").title()} is required', 'error')
                    return render_template('auth/register.html')
            
            # Check if username already exists
            if UserModel.check_username_exists(user_data['username']):
                flash('Username already exists', 'error')
                return render_template('auth/register.html')
            
            # Check if email already exists
            if UserModel.check_email_exists(user_data['email']):
                flash('Email already exists', 'error')
                return render_template('auth/register.html')
            
            # Create user
            success, message, user_id = UserModel.create_user(user_data)
            
            if success:
                flash('User created successfully!', 'success')
                return redirect(url_for('principal.manage_users'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            logging.error(f"Error registering user: {e}")
            flash('An error occurred while creating the user.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = UserModel.get_user_by_id(session['user_id'])
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        try:
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            # Validate passwords
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return render_template('auth/change_password.html')
            
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('auth/change_password.html')
            
            # Change password
            success, message = UserModel.change_password(
                session['user_id'], old_password, new_password
            )
            
            if success:
                flash('Password changed successfully!', 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash(message, 'error')
                
        except Exception as e:
            logging.error(f"Error changing password: {e}")
            flash('An error occurred while changing the password.', 'error')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password (placeholder for future implementation)"""
    if request.method == 'POST':
        email = request.form['email']
        # TODO: Implement password reset functionality
        flash('Password reset functionality will be implemented soon.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Redirect to appropriate dashboard based on role"""
    if session['role'] == 'principal':
        return redirect(url_for('principal.dashboard'))
    else:
        return redirect(url_for('teacher.dashboard'))

# Session management
@auth_bp.route('/session/refresh', methods=['POST'])
@login_required
def refresh_session():
    """Refresh user session"""
    try:
        # Update session timestamp
        session.permanent = True
        return {'success': True, 'message': 'Session refreshed'}
    except Exception as e:
        logging.error(f"Error refreshing session: {e}")
        return {'success': False, 'error': 'Failed to refresh session'}

@auth_bp.route('/session/check')
@login_required
def check_session():
    """Check if session is valid"""
    return {
        'valid': True,
        'user_id': session['user_id'],
        'username': session['username'],
        'role': session['role']
    }
