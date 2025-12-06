"""
Application configuration management using Pydantic Settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All sensitive configuration should be provided via environment variables
    and never hard-coded in the application.
    """
    
    
    DATABASE_URL: str
    
  
    S3_ENDPOINT: str
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str = "us-east-1"
    
    
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    
    
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_EXTENSIONS: str = "pdf,docx"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
 
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes for file size validation."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions into a list."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"



settings = Settings()