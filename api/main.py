from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import auth, transactions, ai, analytics, categories, debts, limits, subscriptions
from .payment.router import router as payment_router

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
    title="Baraka Ai - Personal Finance Tracker",
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
app.include_router(payment_router)
app.include_router(subscriptions.router)


from fastapi import Request
from jose import jwt

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests with user info if available."""
    user_info = "Guest"
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm], options={"verify_signature": False})
            user_id = payload.get("sub")
            user_name = payload.get("name")
            
            if user_id:
                # If name not in token (old token), fetch from DB
                if not user_name:
                    from .database import AsyncSessionLocal
                    from .models.user import User
                    from sqlalchemy import select
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(select(User.name).where(User.id == user_id))
                        user_name = result.scalar_one_or_none()
                
                user_info = f"User:[{user_id} | {user_name or 'Unknown'}]"
    except Exception:
        pass # Fail silently for logging

    response = await call_next(request)
    
    logging.info(f"📡 API [{user_info}]: {request.method} {request.url.path} -> {response.status_code}")
    
    return response


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
