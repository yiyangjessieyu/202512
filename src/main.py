"""
Main FastAPI application entry point for Instagram Content Analyzer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.api.routes import auth, content, query

# Get application settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Instagram Content Analyzer",
    description="AI-powered system for analyzing saved Instagram content",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"message": "Instagram Content Analyzer API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "instagram-content-analyzer"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )