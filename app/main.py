from operator import ge
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import engine, Base
from .api import auth, posts, users, communities, notifications, gemini
from .middleware.cors import setup_cors
from .core.errors import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.environment == "dev" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Relay API server")
    
    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Relay API server")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Relay API",
    description="Campus discovery platform backend",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "dev" else None,
    redoc_url="/redoc" if settings.environment == "dev" else None,
    lifespan=lifespan,
)

# Setup middleware
setup_cors(app)
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(posts.router, prefix="/posts", tags=["Posts"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(communities.router, prefix="/communities", tags=["Communities"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(gemini.router, prefix="/ai", tags=["AI"])

@app.get("/")
async def root():
    return {
        "message": "Relay API",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment == "dev" else None,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)