"""
Initial migration - create documents table.

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create documents table with all required fields.
    """
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=True),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
   
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_s3_key', 'documents', ['s3_key'], unique=True)


def downgrade() -> None:
    """
    Drop documents table and indexes.
    """
    op.drop_index('ix_documents_s3_key', table_name='documents')
    op.drop_index('ix_documents_id', table_name='documents')
    op.drop_table('documents')