from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import auth, transactions, ai, analytics, categories, debts, limits

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logging.info("🚀 Starting AI Accountant API...")
    await init_db()
    logging.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logging.info("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Midas AI - Personal Finance Tracker",
    description="Smart AI-powered expense tracking",
    version="1.0.0",
    root_path="/midas-api",  # For Swagger to work behind nginx
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(categories.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(debts.router)
app.include_router(limits.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Accountant API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected"  # TODO: Add actual DB ping
    }
