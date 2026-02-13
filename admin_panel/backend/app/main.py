from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .core.config import get_settings
from .database import engine, get_db, AsyncSessionLocal
from .models.admin import AdminUser
from .core.security import get_password_hash
from . import models # Register all models
from .routers import auth, users, analytics

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB (create tables if not exist, though we expect them to be managed by Alembic mostly, 
    # but Admin table is new and specific to this service maybe? 
    # No, we should assume shared DB. But AdminUser table needs to exist.
    # For simplicity, we'll auto-create AdminUser table here if it doesn't exist, 
    # as we don't assume the main app has Alembic migrations for *Admin* users yet.)
    # Actually, proper way is to use Alembic in main app. 
    # But since this is "isolated", let's create tables here for admin stuff.
    
    from .database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Create default admin if not exists
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AdminUser).where(AdminUser.email == settings.first_admin_email))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print(f"DTO Creating default admin: {settings.first_admin_email}")
            new_admin = AdminUser(
                email=settings.first_admin_email,
                hashed_password=get_password_hash(settings.first_admin_password),
                is_super_admin=True
            )
            db.add(new_admin)
            await db.commit()
            
    yield

app = FastAPI(
    title="Baraka Admin Panel API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS - Allow Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/api/health")
async def health():
    return {"status": "ok"}
