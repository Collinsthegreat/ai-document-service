"""
File validation utilities for secure file handling.
"""
import os
import re
from typing import Tuple
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import (
    FileSizeExceededError,
    InvalidFileTypeError,
    FileValidationError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues.
    
    Args:
        filename: Original filename from upload.
        
    Returns:
        Sanitized filename safe for storage.
        
    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        'passwd'
        >>> sanitize_filename("invoice (1).pdf")
        'invoice_1.pdf'
    """
    
    filename = os.path.basename(filename)
 
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    
   
    filename = filename.strip('._')
    
  
    if not filename:
        filename = "unnamed_file"
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Extract and validate file extension.
    
    Args:
        filename: Filename to extract extension from.
        
    Returns:
        Lowercase file extension without dot.
        
    Raises:
        FileValidationError: If file has no extension.
    """
    _, ext = os.path.splitext(filename)
    
    if not ext:
        raise FileValidationError("File must have an extension")
    
   
    return ext[1:].lower()


def validate_file_type(filename: str) -> str:
    """
    Validate that file type is allowed.
    
    Args:
        filename: Filename to validate.
        
    Returns:
        Validated file extension.
        
    Raises:
        InvalidFileTypeError: If file type is not allowed.
    """
    extension = get_file_extension(filename)
    allowed = settings.allowed_extensions_list
    
    if extension not in allowed:
        logger.warning(
            f"Attempted upload of disallowed file type",
            extra={
                "filename": filename,
                "extension": extension,
                "allowed_types": allowed
            }
        )
        raise InvalidFileTypeError(extension, allowed)
    
    return extension


async def validate_file_size(file: UploadFile) -> int:
    """
    Validate uploaded file size.
    
    Args:
        file: FastAPI UploadFile object.
        
    Returns:
        File size in bytes.
        
    Raises:
        FileSizeExceededError: If file exceeds maximum allowed size.
    """
    
    content = await file.read()
    file_size = len(content)
    
 
    await file.seek(0)
    
    max_size = settings.max_file_size_bytes
    
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        logger.warning(
            f"File size exceeded",
            extra={
                "filename": file.filename,
                "size_mb": size_mb,
                "max_size_mb": settings.MAX_FILE_SIZE_MB
            }
        )
        raise FileSizeExceededError(size_mb, settings.MAX_FILE_SIZE_MB)
    
    return file_size


async def validate_upload_file(file: UploadFile) -> Tuple[str, int, str]:
    """
    Perform complete validation on uploaded file.
    
    Args:
        file: FastAPI UploadFile object.
        
    Returns:
        Tuple of (sanitized_filename, file_size, file_extension).
        
    Raises:
        FileValidationError: If any validation fails.
        FileSizeExceededError: If file is too large.
        InvalidFileTypeError: If file type is not allowed.
    """
    if not file or not file.filename:
        raise FileValidationError("No file provided")
    
    
    extension = validate_file_type(file.filename)
    
  
    file_size = await validate_file_size(file)
    
   
    safe_filename = sanitize_filename(file.filename)
    
    logger.info(
        "File validation successful",
        extra={
            "original_filename": file.filename,
            "sanitized_filename": safe_filename,
            "file_size_bytes": file_size,
            "extension": extension
        }
    )
    
    return safe_filename, file_size, extension