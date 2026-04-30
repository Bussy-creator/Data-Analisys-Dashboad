import os
import logging
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file validation, storage, and management."""
    
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file for type and size.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_extension not in self.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size (need to read content to check size)
        # Note: FastAPI's UploadFile is async, size check should be done during read
        
        return True, None
    
    async def save_file(self, file: UploadFile) -> str:
        """
        Save uploaded file to disk.
        
        Returns:
            Path to saved file
        """
        # Validate file
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Create unique filename
        file_extension = file.filename.split('.')[-1].lower()
        safe_filename = f"{os.path.splitext(file.filename)[0]}_{os.urandom(8).hex()}.{file_extension}"
        file_path = os.path.join(self.upload_dir, safe_filename)
        
        # Save file
        try:
            content = await file.read()
            
            # Check file size
            if len(content) > self.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File too large. Maximum size: {self.MAX_FILE_SIZE / (1024*1024)}MB"
                )
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk.
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def cleanup_uploads(self, max_age_hours: int = 24):
        """
        Clean up old uploaded files.
        
        Args:
            max_age_hours: Delete files older than this many hours
        """
        import time
        
        try:
            current_time = time.time()
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_hours * 3600:
                        os.remove(file_path)
                        logger.info(f"Cleaned up old file: {filename}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
