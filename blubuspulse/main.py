"""
Main FastAPI application for BluBus Plus.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
from .database import create_tables
from .routes import operators, documents, auth, health, registration
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


# Create FastAPI instance
app = FastAPI(
    title="BluBus Plus Backend API",
    description="Backend API for BluBus Plus operator onboarding and management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(registration.router)
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
