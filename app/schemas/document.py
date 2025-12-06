"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class DocumentUploadResponse(BaseModel):
    """
    Response schema for document upload endpoint.
    
    Attributes:
        document_id: Unique identifier for the uploaded document.
        filename: Original filename.
        file_size: Size in bytes.
        uploaded_at: Upload timestamp.
        text_preview: First 500 characters of extracted text.
    """
    
    document_id: UUID = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes", ge=0)
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    text_preview: str = Field(
        ...,
        description="Preview of extracted text (first 500 chars)",
        max_length=500
    )
    
    model_config = ConfigDict(from_attributes=True)


class DocumentAnalysisResponse(BaseModel):
    """
    Response schema for document analysis endpoint.
    
    Attributes:
        document_id: Document identifier.
        summary: AI-generated summary (2-3 sentences).
        document_type: Classified document type.
        metadata: Extracted structured metadata.
        analyzed_at: Analysis completion timestamp.
    """
    
    document_id: UUID = Field(..., description="Document identifier")
    summary: str = Field(..., description="AI-generated summary")
    document_type: str = Field(
        ...,
        description="Document classification",
        examples=["invoice", "cv", "report", "letter", "contract", "other"]
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Extracted metadata (dates, entities, amounts, etc.)"
    )
    analyzed_at: datetime = Field(..., description="Analysis timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(BaseModel):
    """
    Complete document information response.
    
    Attributes:
        document_id: Unique identifier.
        filename: Original filename.
        file_size: Size in bytes.
        file_type: File MIME type or extension.
        s3_key: Storage key in S3/MinIO.
        extracted_text: Full extracted text content.
        summary: AI-generated summary (if analyzed).
        document_type: Classified type (if analyzed).
        metadata: Extracted metadata (if analyzed).
        s3_url: Pre-signed URL to download file.
        uploaded_at: Upload timestamp.
        analyzed_at: Analysis timestamp (if analyzed).
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """
    
    document_id: UUID
    filename: str
    file_size: int
    file_type: str
    s3_key: str
    extracted_text: str
    summary: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    s3_url: Optional[str] = Field(
        None,
        description="Pre-signed URL to download the original file"
    )
    uploaded_at: datetime
    analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    
    Attributes:
        error: Error type/category.
        message: Human-readable error message.
        details: Additional error details (optional).
    """
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context"
    )