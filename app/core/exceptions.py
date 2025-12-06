"""
Custom exception classes for the application.

These exceptions provide better error handling and allow for
consistent error responses across the API.
"""


class DocumentServiceException(Exception):
    """Base exception for all document service errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FileValidationError(DocumentServiceException):
    """Raised when file validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class FileSizeExceededError(FileValidationError):
    """Raised when uploaded file exceeds size limit."""
    
    def __init__(self, size_mb: float, max_size_mb: int):
        message = f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        super().__init__(message)


class InvalidFileTypeError(FileValidationError):
    """Raised when uploaded file type is not allowed."""
    
    def __init__(self, file_type: str, allowed_types: list):
        message = f"File type '{file_type}' not allowed. Supported types: {', '.join(allowed_types)}"
        super().__init__(message)


class TextExtractionError(DocumentServiceException):
    """Raised when text extraction from document fails."""
    
    def __init__(self, message: str, filename: str):
        full_message = f"Failed to extract text from '{filename}': {message}"
        super().__init__(full_message, status_code=422)


class PDFExtractionError(TextExtractionError):
    """Raised when PDF text extraction fails."""
    pass


class DocxExtractionError(TextExtractionError):
    """Raised when DOCX text extraction fails."""
    pass


class StorageError(DocumentServiceException):
    """Raised when S3/MinIO storage operations fail."""
    
    def __init__(self, message: str, operation: str):
        full_message = f"Storage operation '{operation}' failed: {message}"
        super().__init__(full_message, status_code=500)


class DocumentNotFoundError(DocumentServiceException):
    """Raised when requested document is not found."""
    
    def __init__(self, document_id: str):
        message = f"Document with ID '{document_id}' not found"
        super().__init__(message, status_code=404)


class LLMServiceError(DocumentServiceException):
    """Raised when LLM API call fails."""
    
    def __init__(self, message: str, provider: str = "OpenRouter"):
        full_message = f"{provider} API error: {message}"
        super().__init__(full_message, status_code=502)


class DatabaseError(DocumentServiceException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: str):
        full_message = f"Database operation '{operation}' failed: {message}"
        super().__init__(full_message, status_code=500)