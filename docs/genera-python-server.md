# FastAPI Backend Implementation Guide - Hello World Edition

## Architecture Overview

This guide demonstrates how to implement a production-ready FastAPI backend with AWS Lambda support, using a simple Hello World application that includes user management as a practical example.

## Tech Stack

- **FastAPI + Python** - Modern web framework with automatic API documentation
- **SQLAlchemy ORM + PostgreSQL** - Powerful database layer with type safety
- **Alembic** - Database migration management
- **AWS Lambda + Mangum** - Serverless deployment
- **Pydantic** - Data validation and serialization
- **Boto3** - AWS services integration (S3, SES, Secrets Manager)

## Project Structure

```
app/
├── configuration/          # Configuration classes
│   ├── fast_api_config.py # Main app configuration
│   ├── database_connection.py # Database connection & session management
│   └── app_config.py      # Environment variables handler
├── controllers/           # HTTP request handlers (FastAPI routers)
│   ├── hello_controller.py # Hello World endpoints
│   └── user_controller.py  # User management
├── services/              # Business logic layer
│   ├── hello_service.py    # Hello World business logic
│   ├── user_service.py     # User management logic
│   └── email_service.py    # Email notifications
├── repositories/          # Data access layer
│   └── user_repository.py  # User data access
├── models/                # SQLAlchemy ORM models
│   ├── base.py            # Base model with common fields
│   └── user.py            # User entity
├── dtos/                  # Data Transfer Objects (Pydantic)
│   ├── requests/          # Request DTOs
│   │   └── user_request_dto.py
│   └── responses/         # Response DTOs
│       ├── hello_response.py
│       └── user_response.py
├── enums/                 # Enumerations
│   └── user_status.py
├── exceptions/            # Custom exceptions
│   └── user_not_found_exception.py
├── utils/                 # Utility functions
│   └── encryption.py
├── templates/             # Jinja2 templates (for emails)
│   └── welcome_email.html
└── main.py               # Application entry point
```

## Core Configuration Classes

### 1. FastApiConfig.py
Main application configuration class that handles:
- FastAPI app creation with automatic OpenAPI documentation
- CORS configuration
- Controller registration
- Middleware setup

```python
import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.controllers.hello_controller import HelloController
from app.controllers.user_controller import UserController


class FastApiConfig:
    def __init__(self):
        self.app = self._create_app()
        self._configure_cors()
        self._register_controllers()

    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title="Hello World API",
            description="Simple Hello World API with user management",
            version="1.0.0",
            docs_url="/docs",
            redoc_url=None,
            openapi_url="/openapi.json",
        )
        return app

    def _configure_cors(self):
        origins = self._get_allowed_origins()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            max_age=600,
        )

    def _get_allowed_origins(self) -> list[str]:
        """Configure allowed CORS origins based on environment"""
        default_origins = [
            "http://localhost:3000",
            "http://localhost:5000",
            "https://yourdomain.com",
        ]
        
        # Add CloudFront or custom domain from environment
        cloudfront_url = os.getenv("CLOUDFRONT_URL")
        if cloudfront_url:
            default_origins.append(cloudfront_url)
        
        return default_origins

    def _register_controllers(self):
        """Register all controllers with the FastAPI app"""
        HelloController(self.app)
        UserController(self.app)

    def get_app(self) -> FastAPI:
        return self.app
```

### 2. Database Configuration
SQLAlchemy setup with connection pooling and context manager:

```python
import logging
from typing import Optional

import psycopg
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.configuration.app_config import AppConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    session: Optional[Session] = None

    def __init__(self):
        if not DatabaseConnection._engine:
            DatabaseConnection._engine = self._create_engine()
            DatabaseConnection._session_factory = sessionmaker(
                bind=DatabaseConnection._engine,
                expire_on_commit=False,
            )

    def __enter__(self):
        if DatabaseConnection._session_factory is None:
            raise RuntimeError("Database not initialized")
        self.session = DatabaseConnection._session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                self.session.rollback()
                logger.error(f"Rolling back transaction due to: {exc_type}")
            else:
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error during session cleanup: {e}")
        finally:
            self.session.close()

    @staticmethod
    def _create_engine() -> Engine:
        try:
            host = AppConfig.get_key("database.host")
            port = AppConfig.get_key("database.port", 5432)
            username = AppConfig.get_key("database.username")
            password = AppConfig.get_key("database.password")
            dbname = AppConfig.get_key("database.dbname")

            if not all([host, username, password, dbname]):
                raise ValueError("Missing required database credentials")

            connection_string = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{dbname}"
            logger.info(f"Using database connection: {host}:{port}")

            def _creator():
                conn = psycopg.connect(
                    host=host,
                    port=int(port),
                    user=username,
                    password=password,
                    dbname=dbname,
                    prepare_threshold=None,
                )
                return conn

            engine = create_engine(
                "postgresql+psycopg://",
                creator=_creator,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=5,
                pool_pre_ping=True,
                pool_timeout=30,
                echo=False,
            )

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")

            return engine

        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

    @classmethod
    def from_session(cls, session: Session):
        """Create an instance that shares an existing session.
        
        Used when multiple repositories need to participate in the same
        transaction (e.g., upserting related entities).
        """
        instance = cls.__new__(cls)
        instance.session = session
        return instance

    @classmethod
    def close_all(cls):
        if cls._engine:
            cls._engine.dispose()
            logger.info("All database connections closed")
```

### 3. App Configuration
Simple environment variable handler with dot notation support:

```python
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """Simple configuration client using environment variables"""

    @classmethod
    def get_key(cls, key: str, default: Any = None) -> Any:
        """
        Get configuration value from environment variables
        
        Supports dot notation:
        - get_key("database.host") -> DATABASE_HOST
        - get_key("database.port", 5432) -> DATABASE_PORT with default
        
        Args:
            key: Configuration key in dot notation
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        env_key = key.replace(".", "_").upper()
        value = os.getenv(env_key)
        
        if value is None:
            return default
            
        # Try to convert to int if it looks like a number
        if isinstance(default, int) and value.isdigit():
            return int(value)
            
        return value
```

## Architecture Patterns

### 1. Clean Architecture Layers

**Controllers** → **Services** → **Repositories** → **Database**

- **Controllers**: Handle HTTP requests, validation, and responses (FastAPI routers)
- **Services**: Implement business logic and orchestrate operations
- **Repositories**: Abstract data access with SQLAlchemy
- **Models**: SQLAlchemy ORM entities (database tables)
- **DTOs**: Pydantic models for request/response validation
- **Mappers**: Transform between entities and DTOs

### 2. Controller Pattern
FastAPI router-based controllers with automatic OpenAPI documentation:

```python
# controllers/hello_controller.py
from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Body

from app.dtos.responses.hello_response import HelloResponse, MessageResponse
from app.services import hello_service


class HelloController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/hello",
            response_model=HelloResponse,
            tags=["hello"],
            summary="Get hello world message",
        )
        async def get_hello():
            try:
                message = hello_service.get_hello_message()
                return HelloResponse(
                    message=message,
                    timestamp=datetime.utcnow().isoformat()
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/hello/user/{name}",
            response_model=HelloResponse,
            tags=["hello"],
            summary="Get personalized hello message",
        )
        async def get_hello_user(
            name: Annotated[str, Path(description="User name")],
        ):
            try:
                message = hello_service.get_personalized_hello(name)
                return HelloResponse(
                    message=message,
                    user=name,
                    timestamp=datetime.utcnow().isoformat()
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/hello/message",
            response_model=MessageResponse,
            tags=["hello"],
            summary="Process a message",
        )
        async def post_message(
            body: dict = Body(..., example={"message": "Hello from client"}),
        ):
            try:
                message = body.get("message", "")
                response = hello_service.process_message(message)
                return MessageResponse(
                    response=response,
                    timestamp=datetime.utcnow().isoformat()
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))


# controllers/user_controller.py
from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

from app.dtos.requests.user_request_dto import UserRequestDTO
from app.dtos.responses.user_response import UserResponse
from app.services import user_service


class UserController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/users/{user_id}",
            response_model=UserResponse,
            tags=["users"],
            summary="Get user by ID",
        )
        async def get_user(
            user_id: Annotated[str, Path(description="User ID")],
        ):
            try:
                user = user_service.get_user(user_id)
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                return user
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/users",
            response_model=UserResponse,
            status_code=201,
            tags=["users"],
            summary="Create a new user",
        )
        async def create_user(body: UserRequestDTO):
            try:
                return user_service.create_user(body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.put(
            "/users/{user_id}",
            response_model=UserResponse,
            tags=["users"],
            summary="Update an existing user",
        )
        async def update_user(
            user_id: Annotated[str, Path(description="User ID")],
            body: UserRequestDTO,
        ):
            try:
                return user_service.update_user(user_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
```

### 3. Service Layer Pattern
Business logic with simple hello world and user management:

```python
# services/hello_service.py
def get_hello_message() -> str:
    """Get basic hello world message"""
    return "Hello, World! Welcome to our FastAPI + Lambda application."


def get_personalized_hello(name: str) -> str:
    """Get personalized hello message"""
    if not name or name.strip() == '':
        return "Hello, Anonymous! Welcome to our application."
    return f"Hello, {name}! Welcome to our FastAPI + Lambda application."


def process_message(message: str) -> str:
    """Process a message and return a response"""
    if not message:
        return "I received an empty message. Please send something!"
    
    word_count = len(message.split())
    return f'I received your message: "{message}". It contains {word_count} word(s). Thank you!'


# services/user_service.py
from typing import Optional
import uuid

from app.repositories.user_repository import UserRepository
from app.dtos.requests.user_request_dto import UserRequestDTO
from app.dtos.responses.user_response import UserResponse
from app.models.user import User


def get_user(user_id: str) -> Optional[UserResponse]:
    """Get a user by ID"""
    with UserRepository() as repo:
        user = repo.find_by_id(user_id)
        if not user:
            return None
        return _map_user(user)


def create_user(dto: UserRequestDTO) -> UserResponse:
    """Create a new user"""
    with UserRepository() as repo:
        # Validate business rules
        _validate_user_data(dto)
        
        # Check if email already exists
        existing = repo.find_by_email(dto.email)
        if existing:
            raise ValueError(f"User with email {dto.email} already exists")
        
        # Create entity
        user = User(
            id=str(uuid.uuid4()),
            email=dto.email,
            user_name=dto.user_name,
            first_name=dto.first_name,
            last_name=dto.last_name,
            is_active=True,
        )
        
        # Save to database
        saved_user = repo.save(user)
        
        return _map_user(saved_user)


def update_user(user_id: str, dto: UserRequestDTO) -> UserResponse:
    """Update an existing user"""
    with UserRepository() as repo:
        user = repo.find_by_id(user_id)
        if not user:
            raise LookupError(f"User {user_id} not found")
        
        # Validate business rules
        _validate_user_data(dto)
        
        # Update fields
        if dto.user_name is not None:
            user.user_name = dto.user_name
        if dto.first_name is not None:
            user.first_name = dto.first_name
        if dto.last_name is not None:
            user.last_name = dto.last_name
        if dto.email is not None:
            # Check if new email is already taken by another user
            existing = repo.find_by_email(dto.email)
            if existing and existing.id != user_id:
                raise ValueError(f"Email {dto.email} is already taken")
            user.email = dto.email
        
        # Save changes
        updated_user = repo.save(user)
        
        return _map_user(updated_user)


def _validate_user_data(dto: UserRequestDTO) -> None:
    """Validate user business rules"""
    if dto.email and '@' not in dto.email:
        raise ValueError("Invalid email format")
    
    if dto.user_name and len(dto.user_name.strip()) == 0:
        raise ValueError("Username cannot be empty")


def _map_user(user: User) -> UserResponse:
    """Map User entity to UserResponse DTO"""
    return UserResponse(
        id=user.id,
        email=user.email,
        user_name=user.user_name,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_on,
        updated_at=user.updated_on,
    )
```

### 4. Repository Pattern
Data access abstraction with SQLAlchemy:

```python
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user {user_id}: {e}", exc_info=True)
            raise

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email"""
        try:
            stmt = select(User).where(User.email == email)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding user by email {email}: {e}", exc_info=True)
            raise

    def save(self, user: User) -> User:
        """Save or update a user"""
        try:
            user = self.session.merge(user)
            self.session.flush()
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error saving user: {e}", exc_info=True)
            raise
```

## Lambda Integration

### 1. Lambda Entry Point (main.py)
Handles AWS Lambda events with Mangum:

```python
from dotenv import load_dotenv

load_dotenv()

from mangum import Mangum
from app.configuration.fast_api_config import FastApiConfig

app = FastApiConfig().get_app()

# Mangum handler for AWS Lambda (API Gateway events)
handler = Mangum(app)


def lambda_handler(event, context):
    """AWS Lambda entry point — routes HTTP events through Mangum/FastAPI."""
    return handler(event, context)


# Local execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Dockerfile for Lambda
Production-ready Lambda container:

```dockerfile
FROM public.ecr.aws/lambda/python:3.9

# UTF-8 configuration
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install system dependencies if needed (e.g., wkhtmltopdf for PDFs)
RUN yum -y swap openssl-snapsafe-libs openssl-libs \
    && yum -y install wget fontconfig freetype libX11 libXext libXrender \
    && yum clean all

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy only the application code
COPY app/ ${LAMBDA_TASK_ROOT}/app/

# Lambda handler
CMD ["app.main.lambda_handler"]
```

## Database Schema (SQLAlchemy)

### 1. Base Model
Common fields and timestamp mixin:

```python
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class TimestampMixin:
    """Mixin for created_on and updated_on timestamps"""
    created_on: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_on: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### 2. Entity Example
User entity with SQLAlchemy 2.0 style:

```python
from __future__ import annotations

from typing import Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User entity mapping to users table"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

## Validation & DTOs (Pydantic)

### 1. Request DTOs
Input validation with Pydantic:

```python
# dtos/requests/user_request_dto.py
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserRequestDTO(BaseModel):
    """Request DTO for creating/updating users"""
    email: str = Field(..., description="User email address")
    user_name: str = Field(..., min_length=1, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @field_validator('user_name')
    @classmethod
    def validate_user_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "user_name": "johndoe",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
```

### 2. Response DTOs
Output serialization with Pydantic:

```python
# dtos/responses/hello_response.py
from typing import Optional
from pydantic import BaseModel, Field


class HelloResponse(BaseModel):
    """Response DTO for hello world endpoints"""
    message: str = Field(..., description="Hello message")
    user: Optional[str] = Field(None, description="User name if personalized")
    timestamp: str = Field(..., description="Response timestamp")


class MessageResponse(BaseModel):
    """Response DTO for message processing"""
    response: str = Field(..., description="Processed message response")
    timestamp: str = Field(..., description="Response timestamp")


# dtos/responses/user_response.py
from datetime import datetime
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """Response DTO for user data"""
    id: str
    email: str
    user_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
```

## AWS Services Integration

### 1. Email Service with AWS SES
Template-based email system:

```python
# services/email_service.py
import os
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@yourdomain.com')
        
        # Setup Jinja2 for email templates
        self.jinja_env = Environment(
            loader=FileSystemLoader('app/templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def send_welcome_email(
        self,
        to_email: str,
        first_name: str,
        last_name: Optional[str] = None,
        language: str = 'en'
    ) -> bool:
        """Send welcome email to new user"""
        try:
            full_name = f"{first_name} {last_name}" if last_name else first_name
            
            # Get email content
            subject, html_body = self._get_welcome_email_content(
                full_name, language
            )
            
            # Send email via SES
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                    }
                }
            )
            
            logger.info(f"Welcome email sent to {to_email}: {response['MessageId']}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to send welcome email to {to_email}: {e}")
            return False

    def _get_welcome_email_content(
        self, full_name: str, language: str = 'en'
    ) -> tuple[str, str]:
        """Get welcome email subject and HTML body"""
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        if language == 'es':
            subject = '¡Bienvenido a nuestra aplicación!'
            template = self.jinja_env.get_template('welcome_email_es.html')
        else:
            subject = 'Welcome to our application!'
            template = self.jinja_env.get_template('welcome_email.html')
        
        html_body = template.render(
            full_name=full_name,
            frontend_url=frontend_url
        )
        
        return subject, html_body
```

### 2. AWS Secrets Manager
Secure credential management:

```python
# services/aws_secrets_service.py
import json
import logging
import os
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AWSSecretsService:
    def __init__(self):
        self.client = boto3.client(
            'secretsmanager',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secret value from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                # Binary secret (not common for config)
                return {'binary': response['SecretBinary']}
                
        except ClientError as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise

    def get_database_credentials(self) -> Dict[str, str]:
        """Get database credentials from Secrets Manager"""
        secret_name = os.getenv('DB_SECRET_NAME', 'prod/database/credentials')
        return self.get_secret(secret_name)

    def get_smtp_credentials(self) -> Dict[str, str]:
        """Get SMTP credentials for email service"""
        secret_name = os.getenv('SMTP_SECRET_NAME', 'prod/smtp/credentials')
        return self.get_secret(secret_name)
```

### 3. S3 File Upload Service
Handle file uploads to S3:

```python
# services/s3_service.py
import os
import logging
from typing import Optional
import uuid

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')

    def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        content_type: str = 'application/octet-stream',
        folder: Optional[str] = None
    ) -> Optional[str]:
        """Upload file to S3 and return the URL"""
        try:
            # Generate unique file name
            unique_name = f"{uuid.uuid4()}_{file_name}"
            
            # Add folder prefix if provided
            s3_key = f"{folder}/{unique_name}" if folder else unique_name
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )
            
            # Return the S3 URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            logger.info(f"File uploaded to S3: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
```

## Email Templates (Jinja2)

### Welcome Email Template
```html
<!-- templates/welcome_email.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hello {{ full_name }}!</h1>
        <p>Welcome to our platform. We're excited to have you on board!</p>
        <p>Get started by completing your profile setup:</p>
        <p>
            <a href="{{ frontend_url }}/setup" class="button">Complete Setup</a>
        </p>
        <p>If you have any questions, feel free to reach out to our support team.</p>
        <p>Best regards,<br>The Team</p>
    </div>
</body>
</html>
```

## Database Migrations (Alembic)

### 1. Alembic Configuration
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.models.base import Base
from app.configuration.app_config import AppConfig

# Import all models to ensure they're registered
from app.models.user import User

config = context.config

# Set database URL from environment
config.set_main_option(
    'sqlalchemy.url',
    f"postgresql://{AppConfig.get_key('database.username')}:"
    f"{AppConfig.get_key('database.password')}@"
    f"{AppConfig.get_key('database.host')}:"
    f"{AppConfig.get_key('database.port', 5432)}/"
    f"{AppConfig.get_key('database.dbname')}"
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

### 2. Migration Commands
```bash
# Generate a new migration
alembic revision --autogenerate -m "create users table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current migration version
alembic current

# Show migration history
alembic history
```

### 3. Example Migration
```python
# alembic/versions/001_create_users_table.py
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('user_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_on', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_on', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

## Development Setup

### 1. Requirements.txt
```txt
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
sqlalchemy>=2.0.0
psycopg[binary]>=3.1.0
python-dotenv>=1.0.0
alembic>=1.13.0
pydantic>=2.0.0
boto3>=1.34.0
mangum>=0.17.0
jinja2>=3.1.0
```

### 2. Environment Variables
```env
# Server Configuration
PORT=8000
ENVIRONMENT=development

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password
DATABASE_DBNAME=helloworld_db

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Email Configuration
FROM_EMAIL=noreply@yourdomain.com

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
CLOUDFRONT_URL=https://your-cloudfront-domain.cloudfront.net

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name

# Secrets Manager (optional)
DB_SECRET_NAME=prod/database/credentials
SMTP_SECRET_NAME=prod/smtp/credentials
```

### 3. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Error Handling

### 1. Custom Exceptions
```python
# exceptions/user_not_found_exception.py
class UserNotFoundException(Exception):
    """Raised when a user is not found"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


# exceptions/validation_exception.py
class ValidationException(Exception):
    """Raised when validation fails"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)
```

### 2. Global Exception Handler
```python
# Add to FastApiConfig class
from fastapi import Request
from fastapi.responses import JSONResponse

def _configure_exception_handlers(self):
    @self.app.exception_handler(UserNotFoundException)
    async def user_not_found_handler(request: Request, exc: UserNotFoundException):
        return JSONResponse(
            status_code=404,
            content={"message": str(exc), "user_id": exc.user_id}
        )

    @self.app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc), "field": exc.field}
        )

    @self.app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
```

## Security Best Practices

### 1. Input Validation
Always use Pydantic models for request validation:

```python
from pydantic import BaseModel, field_validator

class UserRequestDTO(BaseModel):
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower().strip()
```

### 2. SQL Injection Prevention
SQLAlchemy ORM automatically prevents SQL injection:

```python
# Safe - uses parameterized queries
stmt = select(User).where(User.email == email)
user = session.execute(stmt).scalar_one_or_none()

# Avoid raw SQL unless necessary
# If you must use raw SQL, use parameters
from sqlalchemy import text
stmt = text("SELECT * FROM users WHERE email = :email")
result = session.execute(stmt, {"email": email})
```

### 3. Environment Variables
Never hardcode sensitive data:

```python
# Good
database_password = os.getenv('DATABASE_PASSWORD')

# Bad
database_password = 'my_secret_password'
```

### 4. CORS Configuration
Restrict origins in production:

```python
def _get_allowed_origins(self) -> list[str]:
    if os.getenv('ENVIRONMENT') == 'production':
        return [
            "https://yourdomain.com",
            os.getenv('CLOUDFRONT_URL')
        ]
    return ["*"]  # Allow all in development
```

## Deployment Considerations

### 1. Lambda Optimization
- Use Mangum for Express-like Lambda compatibility
- Implement connection pooling for database
- Handle cold starts gracefully
- Environment-specific initialization

### 2. Docker Build for Lambda
```bash
# Build Docker image
docker build -t hello-world-api .

# Tag for ECR
docker tag hello-world-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/hello-world-api:latest

# Push to ECR
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/hello-world-api:latest
```

### 3. SAM Template (AWS Serverless Application Model)
```yaml
# template.yml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  HelloWorldFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      ImageUri: <account-id>.dkr.ecr.<region>.amazonaws.com/hello-world-api:latest
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          DATABASE_HOST: !Ref DatabaseHost
          DATABASE_DBNAME: !Ref DatabaseName
          AWS_REGION: !Ref AWS::Region
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

## Monitoring & Logging

### 1. Structured Logging
```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Structured logging for Lambda
def log_event(event_type: str
## Monitoring & Logging

### 1. Structured Logging
```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Structured logging for Lambda
def log_event(event_type: str, data: dict):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data
    }
    logger.info(json.dumps(log_entry))
```

### 2. Request Logging Middleware
```python
# Add to FastApiConfig class
import time
from fastapi import Request

@self.app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {duration:.3f}s"
    )
    
    return response
```

### 3. Health Check Endpoint
```python
# Add to FastApiConfig or create a separate controller
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development")
    }
```

## Utility Functions

### 1. Encryption Utilities
```python
# utils/encryption.py
import os
import hashlib
import base64
from cryptography.fernet import Fernet


def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY not set in environment")
    return base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())


def encrypt(text: str) -> str:
    """Encrypt text using Fernet symmetric encryption"""
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(text.encode())
    return encrypted.decode()


def decrypt(encrypted_text: str) -> str:
    """Decrypt text using Fernet symmetric encryption"""
    f = Fernet(get_encryption_key())
    decrypted = f.decrypt(encrypted_text.encode())
    return decrypted.decode()


def hash_password(password: str) -> str:
    """Hash password using SHA-256 (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed
```

### 2. Date/Time Utilities
```python
# utils/datetime_utils.py
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string"""
    return dt.isoformat()


def from_iso_string(iso_string: str) -> datetime:
    """Parse ISO 8601 string to datetime"""
    return datetime.fromisoformat(iso_string)
```

## Testing

### 1. Unit Tests with pytest
```python
# tests/test_hello_service.py
import pytest
from app.services import hello_service


def test_get_hello_message():
    message = hello_service.get_hello_message()
    assert "Hello, World!" in message


def test_get_personalized_hello():
    message = hello_service.get_personalized_hello("John")
    assert "John" in message


def test_get_personalized_hello_empty_name():
    message = hello_service.get_personalized_hello("")
    assert "Anonymous" in message


def test_process_message():
    response = hello_service.process_message("Hello there")
    assert "2 word(s)" in response
```

### 2. Integration Tests
```python
# tests/test_user_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_user():
    response = client.post(
        "/users",
        json={
            "email": "test@example.com",
            "user_name": "testuser",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["user_name"] == "testuser"


def test_get_user():
    # First create a user
    create_response = client.post(
        "/users",
        json={
            "email": "get@example.com",
            "user_name": "getuser",
            "first_name": "Get",
            "last_name": "User"
        }
    )
    user_id = create_response.json()["id"]
    
    # Then get the user
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
```

### 3. Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_hello_service.py

# Run with verbose output
pytest -v
```

## API Documentation

### 1. Automatic OpenAPI Documentation
FastAPI automatically generates interactive API documentation:

- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc` (if enabled)
- **OpenAPI JSON**: Available at `/openapi.json`

### 2. Enhanced Documentation with Examples
```python
from fastapi import FastAPI, Path, Body
from pydantic import BaseModel, Field


class UserRequestDTO(BaseModel):
    email: str = Field(..., example="user@example.com")
    user_name: str = Field(..., example="johndoe")
    first_name: str = Field(None, example="John")
    last_name: str = Field(None, example="Doe")


@app.post(
    "/users",
    response_model=UserResponse,
    tags=["users"],
    summary="Create a new user",
    description="Create a new user with email, username, and optional name fields.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"}
    }
)
async def create_user(
    body: UserRequestDTO = Body(
        ...,
        example={
            "email": "john.doe@example.com",
            "user_name": "johndoe",
            "first_name": "John",
            "last_name": "Doe"
        }
    )
):
    return user_service.create_user(body)
```

## Hello World Implementation Summary

### 1. Simple API Structure
The Hello World implementation includes:
- **Hello endpoints** - Basic greeting and message processing
- **User management** - CRUD operations for users
- **Email notifications** - Welcome emails via AWS SES
- **Health check** - Service health monitoring

### 2. API Endpoints

**Hello World Endpoints:**
- `GET /hello` - Basic hello world message
- `GET /hello/user/{name}` - Personalized greeting
- `POST /hello/message` - Process user messages

**User Management Endpoints:**
- `GET /users/{user_id}` - Get user by ID
- `POST /users` - Create new user
- `PUT /users/{user_id}` - Update user

**System Endpoints:**
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### 3. Production-Ready Features
- Dual-mode operation (Lambda + local development)
- Comprehensive error handling and logging
- CORS configuration for frontend integration
- Automatic OpenAPI documentation
- Type safety with Pydantic and SQLAlchemy
- Clean architecture with separation of concerns
- Database migrations with Alembic
- AWS services integration (SES, S3, Secrets Manager)

### 4. Extensibility
This Hello World foundation can be easily extended with:
- Additional entities and relationships
- More complex business logic
- External API integrations
- Advanced authentication and authorization
- Real-time features with WebSockets
- Background tasks with Celery
- Caching with Redis

This architecture provides a solid foundation for building scalable FastAPI applications that work seamlessly in both local development and AWS Lambda environments while following clean architecture principles.
