from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, date
import logging

# Import our utilities
from config import Config
from utils.database import db
from utils.face_recognition import face_manager
from utils.qr_code import qr_manager
from utils.logger import get_logger

# Import blueprints
from routes.auth import auth_bp
from routes.api import api_bp
from routes.principal import principal_bp
from routes.teacher import teacher_bp

# Configure logging
logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(principal_bp)
app.register_blueprint(teacher_bp)

# Ensure upload directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.STUDENT_PHOTOS_PATH, exist_ok=True)
os.makedirs(Config.ATTENDANCE_PHOTOS_PATH, exist_ok=True)
os.makedirs(Config.QR_CODES_PATH, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

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

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Main route
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    # Initialize database connection
    db.connect()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)