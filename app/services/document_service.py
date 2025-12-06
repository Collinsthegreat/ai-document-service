"""
Main document service containing business logic.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.services.text_extraction_service import TextExtractionService
from app.services.storage_service import StorageService
from app.services.llm_service import LLMService
from app.core.exceptions import DocumentNotFoundError, DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """
    Main service orchestrating document processing workflow.
    
    Coordinates text extraction, storage, and LLM analysis.
    """
    
    def __init__(self):
        """Initialize document service with dependent services."""
        self.text_extractor = TextExtractionService()
        self.storage = StorageService()
        self.llm = LLMService()
    
    async def upload_document(
        self,
        db: AsyncSession,
        file: UploadFile,
        filename: str,
        file_size: int,
        file_extension: str
    ) -> Document:
        """
        Process and store uploaded document.
        
        Workflow:
        1. Read file content
        2. Extract text from document
        3. Upload file to S3/MinIO
        4. Save document metadata to database
        
        Args:
            db: Database session.
            file: Uploaded file object.
            filename: Sanitized filename.
            file_size: File size in bytes.
            file_extension: File extension (pdf, docx).
            
        Returns:
            Created Document model instance.
            
        Raises:
            TextExtractionError: If text extraction fails.
            StorageError: If file upload to S3 fails.
            DatabaseError: If database operation fails.
        """
        request_id = db.info.get("request_id", "unknown")
        
        logger.info(
            "Starting document upload process",
            extra={
                "file_name": filename,
                "file_size_bytes": file_size,
                "extension": file_extension,
                "request_id": request_id
            }
        )
        
        try:
           
            file_content = await file.read()
            
            
            extracted_text = await self.text_extractor.extract_text(
                file_content,
                filename,
                file_extension
            )
            
            if not extracted_text or len(extracted_text.strip()) == 0:
                logger.warning(
                    "No text extracted from document",
                    extra={"file_name": filename}
                )
            
            
            document = Document(
                filename=filename,
                file_size=file_size,
                file_type=file_extension,
                s3_key="",  
                extracted_text=extracted_text,
                uploaded_at=datetime.utcnow()
            )
            
            db.add(document)
            await db.flush()  
            
          
            s3_key = self.storage.generate_s3_key(filename, str(document.id))
            
            content_type_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
            content_type = content_type_map.get(file_extension, "application/octet-stream")
            
            await self.storage.upload_file(
                file_content=file_content,
                s3_key=s3_key,
                content_type=content_type,
                metadata={
                    "document_id": str(document.id),
                    "original_filename": filename
                }
            )
            
         
            document.s3_key = s3_key
            
            await db.commit()
            await db.refresh(document)
            
            logger.info(
                "Document uploaded successfully",
                extra={
                    "document_id": str(document.id),
                    "file_name": filename,
                    "s3_key": s3_key,
                    "text_length": len(extracted_text),
                    "request_id": request_id
                }
            )
            
            return document
            
        except Exception as e:
            await db.rollback()
            logger.error(
                "Document upload failed",
                extra={
                    "file_name": filename,
                    "error": str(e),
                    "request_id": request_id
                },
                exc_info=True
            )
            raise
    
    async def analyze_document(
        self,
        db: AsyncSession,
        document_id: UUID
    ) -> Document:
        """
        Analyze document using LLM and save results.
        
        Args:
            db: Database session.
            document_id: UUID of document to analyze.
            
        Returns:
            Updated Document model with analysis results.
            
        Raises:
            DocumentNotFoundError: If document doesn't exist.
            LLMServiceError: If LLM analysis fails.
            DatabaseError: If database update fails.
        """
        logger.info(
            "Starting document analysis",
            extra={"document_id": str(document_id)}
        )
        
        try:
           
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                raise DocumentNotFoundError(str(document_id))
            
            
            if document.analyzed_at:
                logger.info(
                    "Document already analyzed",
                    extra={
                        "document_id": str(document_id),
                        "analyzed_at": document.analyzed_at.isoformat()
                    }
                )
                return document
            
            
            summary, document_type, metadata = await self.llm.analyze_document(
                document.extracted_text
            )
            
            
            document.summary = summary
            document.document_type = document_type
            document.metadata_json = metadata
            document.analyzed_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(document)
            
            logger.info(
                "Document analysis completed",
                extra={
                    "document_id": str(document_id),
                    "document_type": document_type,
                    "summary_length": len(summary)
                }
            )
            
            return document
            
        except DocumentNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(
                "Document analysis failed",
                extra={
                    "document_id": str(document_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_document(
        self,
        db: AsyncSession,
        document_id: UUID,
        include_presigned_url: bool = True
    ) -> Document:
        """
        Retrieve document by ID with optional pre-signed URL.
        
        Args:
            db: Database session.
            document_id: UUID of document to retrieve.
            include_presigned_url: Whether to generate S3 pre-signed URL.
            
        Returns:
            Document model instance.
            
        Raises:
            DocumentNotFoundError: If document doesn't exist.
        """
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                raise DocumentNotFoundError(str(document_id))
            
            
            if include_presigned_url and document.s3_key:
                try:
                   
                    document.s3_url = await self.storage.generate_presigned_url(
                        document.s3_key,
                        expiration=3600  
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to generate pre-signed URL",
                        extra={
                            "document_id": str(document_id),
                            "error": str(e)
                        }
                    )
                    document.s3_url = None
            
            return document
            
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to retrieve document",
                extra={
                    "document_id": str(document_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise DatabaseError(str(e), "get_document")