from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging
from contextlib import asynccontextmanager

from app.routes import health_routes, scripting_routes
from app.config import settings
from app.repositories.script_repository import ScriptRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize on startup
    try:
        script_repo = ScriptRepository()
        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
    
    yield
    
    # Cleanup on shutdown
    try:
        script_repo = ScriptRepository()
        script_repo.client.close()
        logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Video Script Generator Service",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(health_routes.router)
    app.include_router(scripting_routes.router, prefix="/api/v1")
    
    # Add root endpoint redirect
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")
    
    return app