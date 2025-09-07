"""
File validation utilities for secure file uploads
"""

import os
import magic
from werkzeug.utils import secure_filename
from PIL import Image
import logging
from config import Config

class FileValidator:
    """Class to handle file validation for uploads"""
    
    def __init__(self):
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.max_file_size = Config.MAX_CONTENT_LENGTH
        self.logger = logging.getLogger(__name__)
    
    def validate_file(self, file, allowed_types=None):
        """
        Validate uploaded file for security and format
        
        Args:
            file: Flask file object
            allowed_types: List of allowed MIME types (optional)
            
        Returns:
            tuple: (is_valid, error_message, file_info)
        """
        try:
            # Check if file exists
            if not file or not file.filename:
                return False, "No file provided", None
            
            # Get file info
            filename = secure_filename(file.filename)
            file_size = len(file.read())
            file.seek(0)  # Reset file pointer
            
            # Check file size
            if file_size > self.max_file_size:
                return False, f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB", None
            
            # Check file extension
            if not self._is_allowed_extension(filename):
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}", None
            
            # Check MIME type using python-magic
            try:
                file_content = file.read(1024)  # Read first 1KB for MIME detection
                file.seek(0)  # Reset file pointer
                mime_type = magic.from_buffer(file_content, mime=True)
                
                if allowed_types and mime_type not in allowed_types:
                    return False, f"MIME type {mime_type} not allowed", None
                
                # Additional validation for images
                if mime_type.startswith('image/'):
                    if not self._validate_image(file):
                        return False, "Invalid or corrupted image file", None
                
            except Exception as e:
                self.logger.warning(f"MIME type detection failed: {e}")
                # Fallback to extension-based validation
                pass
            
            file_info = {
                'filename': filename,
                'size': file_size,
                'mime_type': mime_type if 'mime_type' in locals() else 'unknown'
            }
            
            return True, None, file_info
            
        except Exception as e:
            self.logger.error(f"File validation error: {e}")
            return False, f"File validation failed: {str(e)}", None
    
    def _is_allowed_extension(self, filename):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.allowed_extensions
    
    def _validate_image(self, file):
        """Validate image file integrity"""
        try:
            # Try to open image with PIL
            file.seek(0)
            with Image.open(file) as img:
                img.verify()  # Verify image integrity
            file.seek(0)  # Reset file pointer
            return True
        except Exception as e:
            self.logger.warning(f"Image validation failed: {e}")
            return False
    
    def sanitize_filename(self, filename):
        """Sanitize filename for safe storage"""
        return secure_filename(filename)
    
    def get_safe_path(self, upload_dir, filename):
        """Get safe file path for upload"""
        safe_filename = self.sanitize_filename(filename)
        return os.path.join(upload_dir, safe_filename)

# Global file validator instance
file_validator = FileValidator()