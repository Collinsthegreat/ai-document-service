"""
API endpoints for document operations.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentAnalysisResponse,
    DocumentDetailResponse,
    ErrorResponse
)
from app.services.document_service import DocumentService
from app.utils.file_validators import validate_upload_file
from app.core.exceptions import (
    DocumentServiceException,
    DocumentNotFoundError,
    FileValidationError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def upload_document(
    file: UploadFile = File(..., description="PDF or DOCX file to upload (max 5MB)"),
    db: AsyncSession = Depends(get_db)
) -> DocumentUploadResponse:
    """
    Upload and process a document.
    
    Accepts PDF or DOCX files (max 5MB), extracts text content,
    stores the file in S3/MinIO, and saves metadata to database.
    
    Args:
        file: Uploaded file (PDF or DOCX).
        db: Database session (injected).
        
    Returns:
        Document upload confirmation with preview.
        
    Raises:
        HTTPException: If validation or processing fails.
    """
    try:
        
        filename, file_size, file_extension = await validate_upload_file(file)
        
       
        document_service = DocumentService()
        document = await document_service.upload_document(
            db=db,
            file=file,
            filename=filename,
            file_size=file_size,
            file_extension=file_extension
        )
        
        
        text_preview = document.extracted_text[:500] if document.extracted_text else ""
        
        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            uploaded_at=document.uploaded_at,
            text_preview=text_preview
        )
        
    except FileValidationError as e:
        logger.warning(f"File validation failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": "ValidationError", "message": e.message}
        )
    except DocumentServiceException as e:
        logger.error(f"Document processing failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": type(e).__name__, "message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred during upload"
            }
        )


@router.post(
    "/{document_id}/analyze",
    response_model=DocumentAnalysisResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        502: {"model": ErrorResponse, "description": "LLM service error"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def analyze_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DocumentAnalysisResponse:
    """
    Analyze a document using AI/LLM.
    
    Sends the document's extracted text to OpenRouter LLM for analysis,
    generating a summary, classifying document type, and extracting
    structured metadata.
    
    Args:
        document_id: UUID of document to analyze.
        db: Database session (injected).
        
    Returns:
        Analysis results including summary, type, and metadata.
        
    Raises:
        HTTPException: If document not found or analysis fails.
    """
    try:
        document_service = DocumentService()
        document = await document_service.analyze_document(db, document_id)
        
        return DocumentAnalysisResponse(
            document_id=document.id,
            summary=document.summary,
            document_type=document.document_type,
            metadata=document.metadata_json or {},
            analyzed_at=document.analyzed_at
        )
        
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": e.message}
        )
    except DocumentServiceException as e:
        logger.error(f"Document analysis failed: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": type(e).__name__, "message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred during analysis"
            }
        )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DocumentDetailResponse:
    """
    Retrieve complete document information.
    
    Returns all document data including file info, extracted text,
    analysis results (if analyzed), and a pre-signed S3 URL for
    downloading the original file.
    
    Args:
        document_id: UUID of document to retrieve.
        db: Database session (injected).
        
    Returns:
        Complete document information.
        
    Raises:
        HTTPException: If document not found.
    """
    try:
        document_service = DocumentService()
        document = await document_service.get_document(
            db,
            document_id,
            include_presigned_url=True
        )
        
      
        return DocumentDetailResponse(
            document_id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            file_type=document.file_type,
            s3_key=document.s3_key,
            extracted_text=document.extracted_text,
            summary=document.summary,
            document_type=document.document_type,
            metadata=document.metadata_json,
            s3_url=getattr(document, 's3_url', None),
            uploaded_at=document.uploaded_at,
            analyzed_at=document.analyzed_at,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred"
            }
        )