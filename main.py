from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import os

from app.database import engine, Base
from app.routes import (
    auth_router,
    children_router,
    meals_router,
    plans_router,
    reports_router,
    chat_router,
    gamification_router,
    caregiver_router,
    sync_router,
    audio_router
)
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting TinyTummy API...")
    
    # Create database tables (with error handling for testing)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️ Database connection failed (this is normal for testing): {e}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down TinyTummy API...")


# Create FastAPI app
app = FastAPI(
    title="TinyTummy API",
    description="AI-powered Baby Nutrition Tracker API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
# Allow both with/without trailing slash across all routes
app.router.redirect_slashes = True

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include routers
app.include_router(auth_router)
app.include_router(children_router)
app.include_router(meals_router)
app.include_router(plans_router)
app.include_router(reports_router)
app.include_router(chat_router)
app.include_router(gamification_router)
app.include_router(caregiver_router)
app.include_router(sync_router)
app.include_router(audio_router)
app.include_router(nutrition_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to TinyTummy API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tinytummy-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 