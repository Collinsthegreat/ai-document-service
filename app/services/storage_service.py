"""
Service for managing file storage in S3/MinIO.
"""
import uuid
from datetime import timedelta
from typing import Optional

import aioboto3
from botocore.exceptions import ClientError

from app.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    Service for S3/MinIO storage operations.
    
    Handles file uploads, downloads, and URL generation with proper
    error handling and logging.
    """
    
    def __init__(self):
        """Initialize S3 client configuration."""
        self.session = aioboto3.Session()
        self.bucket_name = settings.S3_BUCKET
        self.endpoint_url = settings.S3_ENDPOINT
        self.region = settings.S3_REGION
    
    def _get_client_config(self):
        """Get S3 client configuration."""
        return {
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": self.region,
        }
    
    def generate_s3_key(self, filename: str, document_id: str) -> str:
        """
        Generate unique S3 key for file storage.
        
        Args:
            filename: Original filename.
            document_id: Document UUID.
            
        Returns:
            S3 key in format: documents/{uuid}/{filename}
        """
        return f"documents/{document_id}/{filename}"
    
    async def ensure_bucket_exists(self) -> None:
        """
        Ensure S3 bucket exists, create if it doesn't.
        
        Raises:
            StorageError: If bucket creation fails.
        """
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                try:
                    await s3.head_bucket(Bucket=self.bucket_name)
                    logger.debug(f"Bucket '{self.bucket_name}' exists")
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code")
                    if error_code == "404":
                        
                        logger.info(f"Creating bucket '{self.bucket_name}'")
                        await s3.create_bucket(Bucket=self.bucket_name)
                        logger.info(f"Bucket '{self.bucket_name}' created successfully")
                    else:
                        raise
        except Exception as e:
            logger.error(f"Failed to ensure bucket exists: {str(e)}", exc_info=True)
            raise StorageError(str(e), "ensure_bucket_exists")
    
    async def upload_file(
        self,
        file_content: bytes,
        s3_key: str,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload file to S3/MinIO.
        
        Args:
            file_content: Binary file content.
            s3_key: S3 key/path for the file.
            content_type: MIME type of file.
            metadata: Optional metadata to attach to file.
            
        Returns:
            S3 key of uploaded file.
            
        Raises:
            StorageError: If upload fails.
        """
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                extra_args = {
                    "ContentType": content_type,
                }
                
                if metadata:
                    extra_args["Metadata"] = metadata
                
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    **extra_args
                )
                
                logger.info(
                    "File uploaded to S3 successfully",
                    extra={
                        "s3_key": s3_key,
                        "bucket": self.bucket_name,
                        "size_bytes": len(file_content),
                        "content_type": content_type
                    }
                )
                
                return s3_key
                
        except Exception as e:
            logger.error(
                f"S3 upload failed",
                extra={"s3_key": s3_key, "error": str(e)},
                exc_info=True
            )
            raise StorageError(str(e), "upload_file")
    
    async def get_file(self, s3_key: str) -> bytes:
        """
        Download file from S3/MinIO.
        
        Args:
            s3_key: S3 key/path of the file.
            
        Returns:
            Binary file content.
            
        Raises:
            StorageError: If download fails.
        """
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                # Read file content
                file_content = await response["Body"].read()
                
                logger.info(
                    "File downloaded from S3 successfully",
                    extra={
                        "s3_key": s3_key,
                        "bucket": self.bucket_name,
                        "size_bytes": len(file_content)
                    }
                )
                
                return file_content
                
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                raise StorageError(f"File not found: {s3_key}", "get_file")
            raise StorageError(str(e), "get_file")
        except Exception as e:
            logger.error(
                f"S3 download failed",
                extra={"s3_key": s3_key, "error": str(e)},
                exc_info=True
            )
            raise StorageError(str(e), "get_file")
    
    async def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate pre-signed URL for temporary file access.
        
        Args:
            s3_key: S3 key/path of the file.
            expiration: URL expiration time in seconds (default 1 hour).
            
        Returns:
            Pre-signed URL string.
            
        Raises:
            StorageError: If URL generation fails.
        """
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": s3_key
                    },
                    ExpiresIn=expiration
                )
                
                logger.debug(
                    "Pre-signed URL generated",
                    extra={
                        "s3_key": s3_key,
                        "expiration_seconds": expiration
                    }
                )
                
                return url
                
        except Exception as e:
            logger.error(
                f"Pre-signed URL generation failed",
                extra={"s3_key": s3_key, "error": str(e)},
                exc_info=True
            )
            raise StorageError(str(e), "generate_presigned_url")
    
    async def delete_file(self, s3_key: str) -> None:
        """
        Delete file from S3/MinIO.
        
        Args:
            s3_key: S3 key/path of the file to delete.
            
        Raises:
            StorageError: If deletion fails.
        """
        try:
            async with self.session.client("s3", **self._get_client_config()) as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                logger.info(
                    "File deleted from S3 successfully",
                    extra={"s3_key": s3_key, "bucket": self.bucket_name}
                )
                
        except Exception as e:
            logger.error(
                f"S3 deletion failed",
                extra={"s3_key": s3_key, "error": str(e)},
                exc_info=True
            )
            raise StorageError(str(e), "delete_file")