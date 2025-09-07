import os
import secrets
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # MySQL Database configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'your_password'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'attendance_system'
    MYSQL_CHARSET = 'utf8mb4'
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Face recognition settings
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_DETECTION_MODEL = 'hog'  # 'hog' for CPU, 'cnn' for GPU
    
    # Storage paths
    STUDENT_PHOTOS_PATH = 'static/images/student_photos'
    ATTENDANCE_PHOTOS_PATH = 'static/images/attendance_photos'
    QR_CODES_PATH = 'static/images/qr_codes'
    FACE_ENCODINGS_PATH = 'data/face_encodings.pkl'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # OCR Settings
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD') or '/usr/bin/tesseract'  # Default to Linux path
