"""
Dependency injection for FastAPI endpoints.

Provides database sessions and other shared resources.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import uuid

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=not settings.is_production,  
    pool_pre_ping=True,  
    pool_size=10,
    max_overflow=20,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for dependency injection.
    
    Yields:
        AsyncSession: Database session that will be automatically closed.
        
    Example:
        @app.get("/documents")
        async def get_documents(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            raise
        finally:
            await session.close()


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing.
    
    Returns:
        UUID string for request correlation.
    """
    return str(uuid.uuid4())


async def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in SQLAlchemy models.
    Should be called on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called on application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")