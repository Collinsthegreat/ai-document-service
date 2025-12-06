"""
SQLAlchemy model for document storage.
"""
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.dependencies import Base


class Document(Base):
    """
    Document model for storing uploaded files and their analysis.
    
    Attributes:
        id: Unique identifier (UUID).
        filename: Original filename of uploaded document.
        file_size: Size of file in bytes.
        file_type: MIME type or extension of file.
        s3_key: Key/path of file in S3/MinIO storage.
        extracted_text: Full text extracted from document.
        summary: AI-generated summary (nullable until analyzed).
        document_type: Classified document type (invoice, CV, etc.).
        metadata_json: Additional extracted metadata as JSON.
        uploaded_at: Timestamp when file was uploaded.
        analyzed_at: Timestamp when LLM analysis completed (nullable).
        created_at: Record creation timestamp.
        updated_at: Record last update timestamp.
    """
    
    __tablename__ = "documents"
    
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique document identifier"
    )
    
   
    filename = Column(
        String(255),
        nullable=False,
        doc="Original filename of uploaded document"
    )
    
    file_size = Column(
        Integer,
        nullable=False,
        doc="File size in bytes"
    )
    
    file_type = Column(
        String(50),
        nullable=False,
        doc="File MIME type or extension"
    )
    
    s3_key = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        doc="S3/MinIO storage key"
    )
    
  
    extracted_text = Column(
        Text,
        nullable=False,
        doc="Full text content extracted from document"
    )
    
  
    summary = Column(
        Text,
        nullable=True,
        doc="AI-generated document summary"
    )
    
    document_type = Column(
        String(50),
        nullable=True,
        doc="Classified document type (invoice, CV, report, etc.)"
    )
    
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional extracted metadata (dates, entities, etc.)"
    )
    
    
    uploaded_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Timestamp when document was uploaded"
    )
    
    analyzed_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp when LLM analysis completed"
    )
    
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Record last update timestamp"
    )
    
    def __repr__(self) -> str:
        """String representation of Document model."""
        return f"<Document(id={self.id}, filename={self.filename})>"