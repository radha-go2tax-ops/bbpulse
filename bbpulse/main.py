"""
Main FastAPI application for BluBus Plus.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from .database import create_tables
from .routes import operators, documents, auth, health, registration, unified_profile
from .settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting BluBus Plus API")
    create_tables()
    logger.info("Database tables created/verified")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BluBus Plus API")


# Create FastAPI instance with enterprise-standard OpenAPI configuration
app = FastAPI(
    title="BluBus Pulse API",
    description="""
    ## BluBus Pulse Backend API
    
    A comprehensive API for bus operator onboarding, management, and authentication.
    
    ### Features
    - 🔐 **Multi-channel Authentication**: Email and WhatsApp OTP verification
    - 🚌 **Operator Management**: Complete operator registration and management
    - 📱 **WhatsApp Integration**: Direct WhatsApp communication for operators
    - 📧 **Email Services**: Automated email notifications and OTP delivery
    - 🔒 **Security**: JWT tokens, rate limiting, and input validation
    - 📊 **Document Management**: Secure document upload and verification
    
    ### Authentication
    The API uses JWT tokens for authentication. Include the token in the Authorization header:
    ```
    Authorization: Bearer <your-token>
    ```
    
    ### Rate Limiting
    - OTP Requests: 3 requests per 5 minutes per contact
    - Registration Attempts: 5 attempts per hour per contact
    - Login Attempts: 10 attempts per hour per contact
    
    ### Response Format
    All responses follow a standardized format:
    ```json
    {
      "status": "success|error",
      "code": 200,
      "data": { /* response data */ },
      "meta": {
        "requestId": "uuid-string",
        "timestamp": "2024-01-01T10:00:00Z"
      }
    }
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "BluBus Pulse API Support",
        "email": "support@blubus.com",
        "url": "https://blubus.com/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.blubus.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "authentication",
            "description": "User authentication and OTP verification endpoints",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.blubus.com/auth"
            }
        },
        {
            "name": "operators",
            "description": "Bus operator registration and management",
            "externalDocs": {
                "description": "Operator Guide",
                "url": "https://docs.blubus.com/operators"
            }
        },
        {
            "name": "documents",
            "description": "Document upload and verification for operators",
            "externalDocs": {
                "description": "Document Guide",
                "url": "https://docs.blubus.com/documents"
            }
        },
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "unified-profile",
            "description": "Unified profile management for both general users and operator users",
            "externalDocs": {
                "description": "Profile Management Guide",
                "url": "https://docs.blubus.com/profile"
            }
        }
    ]
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly for production
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler for standardized error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler to return standardized error responses.
    This prevents FastAPI from wrapping our error responses in a 'detail' field.
    """
    # If the detail is already a dict with our standardized format, return it directly
    if isinstance(exc.detail, dict) and "status" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Otherwise, return the default FastAPI format
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(registration.router)
app.include_router(unified_profile.router)
app.include_router(operators.router)
app.include_router(documents.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to BluBus Plus Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

