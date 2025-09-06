#!/usr/bin/env python3
"""
Setup script for Smart Attendance System
This script helps set up the attendance system for rural schools
"""

import os
import sys
import subprocess
import platform
import mysql.connector
from pathlib import Path

class AttendanceSystemSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.project_root = Path(__file__).parent
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🔍 Checking Python version...")
        if self.python_version < (3, 8):
            print("❌ Python 3.8+ is required. Current version:", sys.version)
            return False
        print(f"✅ Python {self.python_version.major}.{self.python_version.minor} is compatible")
        return True
    
    def check_mysql(self):
        """Check if MySQL is installed and running"""
        print("🔍 Checking MySQL installation...")
        try:
            # Try to connect to MySQL
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''  # Try without password first
            )
            connection.close()
            print("✅ MySQL is running and accessible")
            return True
        except mysql.connector.Error as e:
            print(f"❌ MySQL connection failed: {e}")
            print("Please ensure MySQL is installed and running")
            return False
    
    def install_system_dependencies(self):
        """Install system-level dependencies"""
        print("🔧 Installing system dependencies...")
        
        if self.system == "windows":
            self.install_windows_dependencies()
        elif self.system == "linux":
            self.install_linux_dependencies()
        elif self.system == "darwin":  # macOS
            self.install_macos_dependencies()
        else:
            print(f"❌ Unsupported operating system: {self.system}")
            return False
        
        return True
    
    def install_windows_dependencies(self):
        """Install Windows dependencies"""
        print("Installing Windows dependencies...")
        
        # Check if Tesseract is installed
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if not os.path.exists(tesseract_path):
            print("❌ Tesseract OCR not found. Please install from:")
            print("https://github.com/UB-Mannheim/tesseract/wiki")
            return False
        
        print("✅ Tesseract OCR found")
        return True
    
    def install_linux_dependencies(self):
        """Install Linux dependencies"""
        print("Installing Linux dependencies...")
        
        try:
            # Install Tesseract
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "libgl1-mesa-glx"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "libglib2.0-0"], check=True)
            print("✅ Linux dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Linux dependencies: {e}")
            return False
    
    def install_macos_dependencies(self):
        """Install macOS dependencies"""
        print("Installing macOS dependencies...")
        
        try:
            # Install Tesseract using Homebrew
            subprocess.run(["brew", "install", "tesseract"], check=True)
            print("✅ macOS dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install macOS dependencies: {e}")
            print("Please install Homebrew first: https://brew.sh/")
            return False
    
    def create_virtual_environment(self):
        """Create Python virtual environment"""
        print("🔧 Creating virtual environment...")
        
        venv_path = self.project_root / "venv"
        if venv_path.exists():
            print("✅ Virtual environment already exists")
            return True
        
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("✅ Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        print("🔧 Installing Python dependencies...")
        
        venv_python = self.project_root / "venv" / "bin" / "python"
        if self.system == "windows":
            venv_python = self.project_root / "venv" / "Scripts" / "python.exe"
        
        try:
            subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Python dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python dependencies: {e}")
            return False
    
    def setup_database(self):
        """Set up MySQL database"""
        print("🔧 Setting up database...")
        
        try:
            # Connect to MySQL
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''  # Update this with your MySQL password
            )
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database created")
            
            # Import schema
            schema_file = self.project_root / "database" / "schema.sql"
            if schema_file.exists():
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Execute schema
                for statement in schema_sql.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
                
                connection.commit()
                print("✅ Database schema imported")
            
            cursor.close()
            connection.close()
            return True
            
        except mysql.connector.Error as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        print("🔧 Creating directories...")
        
        directories = [
            "static/uploads/temp",
            "static/images/student_photos",
            "static/images/attendance_photos",
            "static/images/qr_codes",
            "data/logs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        
        return True
    
    def create_config_file(self):
        """Create configuration file"""
        print("🔧 Creating configuration file...")
        
        config_content = '''import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
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
    TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Windows
    # TESSERACT_CMD = '/usr/bin/tesseract'  # Linux/Mac
'''
        
        config_file = self.project_root / "config.py"
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print("✅ Configuration file created")
        print("⚠️  Please update database credentials in config.py")
        return True
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting Smart Attendance System Setup")
        print("=" * 50)
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Installing system dependencies", self.install_system_dependencies),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Checking MySQL", self.check_mysql),
            ("Setting up database", self.setup_database),
            ("Creating directories", self.create_directories),
            ("Creating configuration file", self.create_config_file),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        print("\n" + "=" * 50)
        print("🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update database credentials in config.py")
        print("2. Activate virtual environment:")
        if self.system == "windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("3. Run the application:")
        print("   python app.py")
        print("4. Open browser and go to: http://localhost:5000")
        print("\n🔑 Default login credentials:")
        print("   Principal: admin / admin123")
        print("   Teacher: teacher / teacher123")
        
        return True

def main():
    """Main setup function"""
    setup = AttendanceSystemSetup()
    success = setup.run_setup()
    
    if not success:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)
    
    print("\n✅ Setup completed successfully!")

if __name__ == "__main__":
    main()
