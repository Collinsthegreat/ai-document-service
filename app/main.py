"""
Main FastAPI application entry point.
"""
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.dependencies import init_db, close_db
from app.core.exceptions import DocumentServiceException
from app.api.v1.endpoints import documents
from app.services.storage_service import StorageService


setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    
    Handles initialization of database and storage on startup,
    and cleanup on shutdown.
    """
   
    logger.info(
        "Application starting up",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL
        }
    )
    
    try:
        
        await init_db()
        logger.info("Database initialized")
        
        
        storage = StorageService()
        await storage.ensure_bucket_exists()
        logger.info("Storage initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise
    
    yield
    
  
    logger.info("Application shutting down")
    await close_db()
    logger.info("Database connections closed")



app = FastAPI(
    title="AI Document Summarization Service",
    description="Production-ready service for document analysis using AI/LLM",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add unique request ID to each request for tracing.
    
    The request ID is added to the request state and logged
    with all operations during the request lifecycle.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
  
    logger.info(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None
        }
    )
    
    response = await call_next(request)
    
   
    response.headers["X-Request-ID"] = request_id
    
    return response



@app.exception_handler(DocumentServiceException)
async def document_service_exception_handler(
    request: Request,
    exc: DocumentServiceException
):
    """
    Handle custom document service exceptions.
    
    Returns appropriate HTTP status code and error details.
    """
    logger.error(
        f"Document service exception: {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "exception_type": type(exc).__name__,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """
    Handle Pydantic validation errors.
    
    Returns formatted validation error details.
    """
    logger.warning(
        "Request validation failed",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions.
    
    Logs full error details and returns generic error message.
    """
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )



@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "service": "ai-document-service",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }



app.include_router(documents.router, prefix="/api/v1")



@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "AI Document Summarization Service",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=not settings.is_production,
        log_config=None 
    )