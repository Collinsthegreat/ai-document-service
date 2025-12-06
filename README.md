# AI Document Summarization Service

Production-ready FastAPI service for intelligent document analysis using AI/LLM. Upload PDF/DOCX files, extract text, generate summaries, classify document types, and extract structured metadata.

 Features

- Document Upload: Accept PDF and DOCX files (max 5MB)
- Text Extraction: Robust extraction with fallback mechanisms (pdfplumber + PyPDF2)
- Cloud Storage: S3/MinIO integration for secure file storage
- AI Analysis: Groq LLM integration (Llama 3.3 70B) for intelligent analysis
- Metadata Extraction: Automatic extraction of dates, entities, amounts, and key information
- Document Classification: Identify document types (invoice, CV, report, letter, contract, etc.)
- Smart Summaries: Generate concise 2-3 sentence summaries
- Production-Ready: Comprehensive logging, error handling, request tracing, and validation

 Tech Stack

- Framework: FastAPI 0.109+ (async/await, auto-generated API docs)
- Database: PostgreSQL 15+ with AsyncPG
- ORM: SQLAlchemy 2.0 (async)
- Storage: MinIO/AWS S3 (aioboto3 for async operations)
- LLM: Groq API (Llama 3.3 70B Versatile) - **FREE tier**
- Document Processing: PyPDF2, pdfplumber, python-docx
- Migrations: Alembic
- Validation: Pydantic v2
- Retry Logic: Tenacity (exponential backoff for LLM calls)

 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- MinIO or AWS S3 account
- Groq API key (FREE at https://console.groq.com/)

 Quick Start

 1. Clone and Setup

```bash
git clone https://github.com/your-username/ai-document-service.git
cd ai-document-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required Environment Variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/document_service

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=documents
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1

# Groq LLM (FREE)
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

# Application
MAX_FILE_SIZE_MB=5
ALLOWED_EXTENSIONS=pdf,docx
LOG_LEVEL=INFO
ENVIRONMENT=development
HOST=0.0.0.0
PORT=8000
```
 3. Setup Database

```bash
# Create database
createdb document_service

# Run migrations
alembic upgrade head
```

 4. Setup MinIO (Local Development)

```bash
# Using Docker
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"

# Access MinIO Console: http://localhost:9001
# Login: minioadmin / minioadmin
# Create bucket named 'documents'
```

 5. Get Free Groq API Key

1. Visit https://console.groq.com/
2. Sign up (completely free, no credit card required)
3. Go to API Keys section
4. Create new API key
5. Copy and add to `.env` file

 6. Run Application

```bash
# Development mode (with auto-reload)
python -m app.main

# OR using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API:
- API Docs (Swagger): http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/health

 API Endpoints

 1. Upload Document

Upload a PDF or DOCX file for processing.

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

Example:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./DevOps_Roadmap_by_Tech_with_Nana.pdf"
```

Response:
```json
{
  "document_id": "56e15d1f-0dc1-48df-ae3c-85adea98d897",
  "filename": "DevOps_Roadmap_by_Tech_with_Nana.pdf",
  "file_size": 2213078,
  "uploaded_at": "2025-12-06T08:40:22.294962",
  "text_preview": "DEVOPS\nROADMAP\nby TechWorld with Nana\n\nDEVOPS ROADMAP BY..."
}
```

 2. Analyze Document

Send the document to Groq LLM for AI-powered analysis.

```bash
curl -X POST "http://localhost:8000/api/v1/documents/{document_id}/analyze" \
  -H "accept: application/json"
```

Example:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/56e15d1f-0dc1-48df-ae3c-85adea98d897/analyze" \
  -H "accept: application/json"
```

Response:
```json
{
  "document_id": "56e15d1f-0dc1-48df-ae3c-85adea98d897",
  "summary": "This document is a comprehensive DevOps roadmap created by TechWorld with Nana, outlining essential skills and technologies needed for DevOps engineers. It covers topics including software development concepts, Linux basics, containerization, CI/CD pipelines, cloud providers, Kubernetes, monitoring, Infrastructure as Code, scripting languages, and version control.",
  "document_type": "report",
  "metadata": {
    "sender": "TechWorld with Nana",
    "key_entities": [
      "DevOps",
      "Docker",
      "Kubernetes",
      "CI/CD",
      "AWS",
      "Git",
      "Linux",
      "Python",
      "Terraform"
    ],
    "language": "English",
    "topics": [
      "DevOps",
      "Software Development",
      "Cloud Computing",
      "Containerization",
      "Infrastructure as Code"
    ]
  },
  "analyzed_at": "2025-12-06T08:45:30.123456"
}
```

 3. Get Document Details

Retrieve complete document information including pre-signed S3 URL.

```bash
curl -X GET "http://localhost:8000/api/v1/documents/{document_id}" \
  -H "accept: application/json"
```

Example:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/56e15d1f-0dc1-48df-ae3c-85adea98d897" \
  -H "accept: application/json"
```

Response:
```json
{
  "document_id": "56e15d1f-0dc1-48df-ae3c-85adea98d897",
  "filename": "DevOps_Roadmap_by_Tech_with_Nana.pdf",
  "file_size": 2213078,
  "file_type": "pdf",
  "s3_key": "documents/56e15d1f-0dc1-48df-ae3c-85adea98d897/DevOps_Roadmap_by_Tech_with_Nana.pdf",
  "extracted_text": "Full document text content...",
  "summary": "Document summary...",
  "document_type": "report",
  "metadata": {...},
  "s3_url": "http://localhost:9000/documents/56e15d1f-...?X-Amz-Expires=3600",
  "uploaded_at": "2025-12-06T08:40:22.294962",
  "analyzed_at": "2025-12-06T08:45:30.123456",
  "created_at": "2025-12-06T08:40:22.294962",
  "updated_at": "2025-12-06T08:45:30.123456"
}
```


 Project Structure

```
ai-document-service/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management (Pydantic Settings)
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── documents.py     # Document API routes
│   ├── core/
│   │   ├── dependencies.py          # Database session & dependency injection
│   │   ├── exceptions.py            # Custom exception classes
│   │   └── logging.py               # Structured logging configuration
│   ├── models/
│   │   └── document.py              # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── document.py              # Pydantic request/response schemas
│   ├── services/
│   │   ├── document_service.py      # Main business logic orchestration
│   │   ├── text_extraction_service.py # PDF/DOCX text extraction
│   │   ├── storage_service.py       # S3/MinIO file operations
│   │   └── llm_service.py           # Groq LLM integration
│   └── utils/
│       └── file_validators.py       # File validation utilities
├── alembic/
│   ├── versions/                    # Database migration scripts
│   │   └── 001_initial_migration.py
│   └── env.py                       # Alembic environment config
├── tests/                           # Test files
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── alembic.ini                      # Alembic configuration
├── docker-compose.yml               # Docker Compose for local development
├── Dockerfile                       # Production Docker image
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

 Development

Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage report
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/
```

 Code Quality

```bash
# Format code with Black
black app/

# Check linting with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add new column"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

 Docker Deployment

 Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, MinIO, and FastAPI app)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

 Using Dockerfile Directly

```bash
# Build image
docker build -t ai-document-service .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name document-service \
  ai-document-service

# View logs
docker logs -f document-service

# Stop container
docker stop document-service
```

 Environment Variables for Production

```env
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/dbname
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=production-documents
S3_ACCESS_KEY=your_aws_access_key
S3_SECRET_KEY=your_aws_secret_key
S3_REGION=us-east-1
GROQ_API_KEY=your_production_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
MAX_FILE_SIZE_MB=10
HOST=0.0.0.0
PORT=8000
```

 Monitoring & Observability

The service includes comprehensive monitoring features:

- **Structured Logging**: JSON-formatted logs in production for easy parsing
- **Request Tracing**: Unique request IDs (X-Request-ID header) for tracking requests across services
- **Health Check Endpoint**: `/health` for load balancer health checks
- **Error Tracking**: Detailed error logging with stack traces
- **Token Usage Tracking**: Logs Groq API token consumption for cost monitoring

Example structured log:
```json
{
  "timestamp": "2025-12-06T08:40:22.294962",
  "level": "INFO",
  "logger": "app.services.document_service",
  "message": "Document uploaded successfully",
  "document_id": "56e15d1f-0dc1-48df-ae3c-85adea98d897",
  "filename": "document.pdf",
  "file_size_bytes": 2213078,
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

 Troubleshooting

 Common Issues

1. Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL format in .env
# Correct format: postgresql+asyncpg://user:password@host:port/database

# Test connection
psql -h localhost -U postgres -d document_service
```

2. MinIO Connection Error
```bash
# Check MinIO is running
curl http://localhost:9000/minio/health/live

# Verify bucket exists
# Access MinIO Console at http://localhost:9001
# Login with credentials from .env

# Check S3_ENDPOINT has correct protocol (http:// or https://)
```

3. Groq API Error
```bash
# Verify API key is valid
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Check rate limits (30 requests/minute on free tier)
# Review Groq API status: https://status.groq.com/
```

4. File Upload Fails
```bash
# Check file size (must be under 5MB)
ls -lh /path/to/file

# Verify file type (only PDF or DOCX allowed)
file /path/to/file

# Check disk space
df -h

# Review application logs
docker-compose logs app
```

5. Text Extraction Returns Empty
```bash
# PDF might be image-based or encrypted
# Try opening the PDF manually to verify it contains selectable text
# Consider adding OCR support for image-based PDFs (future enhancement)
```

6. Migration Errors
```bash
# Check current migration version
alembic current

# Reset database (WARNING: destroys all data)
alembic downgrade base
alembic upgrade head

# If stuck, manually check alembic_version table
psql -d document_service -c "SELECT * FROM alembic_version;"
```

 Technology Choices Explained

 Why Groq?
- **FREE tier** with generous limits (30 req/min)
- **Fastest inference** speeds in the market (sub-second responses)
- **No credit card required** for getting started
- **Excellent model quality** (Llama 3.3 70B)
- **OpenAI-compatible API** for easy integration

 Why Dual PDF Extraction (pdfplumber + PyPDF2)?
- **pdfplumber**: Better for complex layouts, tables, and multi-column documents
- **PyPDF2**: Lightweight fallback for simple PDFs
- **Automatic fallback**: Ensures maximum text extraction success rate

 Why Async Everything (FastAPI, SQLAlchemy, aioboto3)?
- **Non-blocking I/O**: Handle multiple concurrent uploads without thread blocking
- **Better throughput**: Can process 10+ documents simultaneously
- **Lower resource usage**: More efficient than threading/multiprocessing

 Why Tenacity for Retry Logic?
- **Exponential backoff**: Handles transient LLM API failures gracefully
- **Production-tested**: Prevents cascade failures in distributed systems
- **Configurable**: Easy to adjust retry attempts and backoff timing

 Performance Characteristics

- Concurrent Uploads: Handles 10+ simultaneous document uploads
- Text Extraction: ~1-3 seconds for typical PDFs (50-100 pages)
- LLM Analysis: ~2-5 seconds with Groq (extremely fast)
- Database Queries: <100ms with proper indexing
- S3 Upload: ~500ms - 2 seconds depending on file size and network

 Future Enhancements

- [ ] Batch Processing: Upload and analyze multiple documents at once
- [ ] Document Comparison: Compare two documents and highlight differences
- [ ] More File Formats: Support for DOC, TXT, RTF, HTML
- [ ] OCR Support: Extract text from image-based PDFs
- [ ] User Authentication: JWT-based auth with user management
- [ ] Rate Limiting: Per-user rate limits using Redis
- [ ] Webhooks: Notify external services when analysis completes
- [ ] Document Versioning: Track changes across document versions
- [ ] Full-Text Search: Elasticsearch integration for document search
- [ ] Export Options: Export analysis to JSON, CSV, or Excel



