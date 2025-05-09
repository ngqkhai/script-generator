from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from contextlib import asynccontextmanager
import json
import uuid
from typing import Dict, List, Optional, Any

from app.providers.script_generator import ScriptGenerator
from app.providers.gemini_service import GeminiService
from app.providers.message_broker import ScriptGeneratorMessageBroker
from app.models.request_models import ScriptRequest
from app.repositories.script_repository import ScriptRepository

from app.routes import health_routes, scripting_routes, websocket_routes
from app.config import settings

# Import the connection manager from utils to use a single instance
from app.utils.websocket_manager import connection_manager

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('script_generator.log')
    ]
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
    
    # Initialize services
    script_generator = ScriptGenerator()  # Initialize singleton instance
    message_broker = ScriptGeneratorMessageBroker()
    logger.info("Services initialized, waiting for startup event...")
    
    # Store services in app state
    app.state.script_generator = script_generator
    app.state.message_broker = message_broker
    
    # This function will be registered as a startup event handler
    async def startup_event():
        """Initialize services on startup"""
        logger.info("Starting Script Generator Service")
        try:
            # Connect to RabbitMQ
            await message_broker.connect()
            logger.info("Connected to RabbitMQ")

            # Define message handler
            async def handle_data_collected(message: dict, headers: dict):
                try:
                    logger.info(f"Processing message with source: {message.get('source_name', 'unknown')}")
                    
                    # Create a ScriptRequest object from the message data
                    from app.models.request_models import ScriptRequest
                    
                    # Map message fields to ScriptRequest fields
                    request = ScriptRequest(
                        script_type=message.get("script_type"),
                        target_audience=message.get("target_audience"),
                        duration_seconds=message.get("duration"),  # Note: source uses "duration", target expects "duration_seconds"
                        tone=message.get("tone"),
                        style_description=message.get("style_description"),
                        language=message.get("language"),
                        content=message.get("content")
                    )
                    
                    # Generate script
                    script = await script_generator.generate_script(request)

                    # Add metadata from the message
                    script["collection_id"] = message.get("collection_id")
                    script["source_type"] = message.get("source_type")
                    script["source_name"] = message.get("source_name")
                    
                    # Generate a unique ID for the script if not already present
                    if "_id" not in script:
                        script["_id"] = str(uuid.uuid4())
                    
                    # Store the generated script in MongoDB
                    script_repo = ScriptRepository()
                    result = script_repo.insert_one(script)
                    if result:
                        logger.info(f"Successfully stored script in MongoDB with ID: {script['_id']}")
                        
                        # Send WebSocket notification to clients listening for this collection_id
                        collection_id = message.get("collection_id")
                        logger.info(f"Collection ID: {collection_id}")
                        if collection_id:
                            try:
                                # Add detailed logging before sending notification
                                logger.info(f"Preparing to send WebSocket notification for collection_id: {collection_id}")
                                
                                # Debug dump all connections
                                connection_manager.debug_dump_connections()
                                
                                # Log connection status
                                if collection_id in connection_manager.collection_connections:
                                    conn_count = len(connection_manager.collection_connections[collection_id])
                                    logger.info(f"Found {conn_count} active connections for collection_id: {collection_id}")
                                else:
                                    logger.warning(f"No active connections found for collection_id: {collection_id} before sending notification")
                                    # Create new test connection for collection ID (temporary workaround)
                                    logger.info(f"Collection connections: {list(connection_manager.collection_connections.keys())}")
                                
                                # Prepare the notification message
                                notification = {
                                    "type": "script_generated",
                                    "collection_id": collection_id,
                                    "script_id": script["_id"],
                                    "message": "Script generation completed",
                                    "status": "completed"
                                }
                                logger.info(f"Sending WebSocket notification with payload: {notification}")
                                
                                # Send the notification
                                await connection_manager.send_to_collection(
                                    collection_id,
                                    notification
                                )
                                logger.info(f"Sent WebSocket notification for collection_id: {collection_id}")
                            except Exception as ws_err:
                                logger.error(f"WebSocket notification error: {str(ws_err)}")
                                logger.exception("Detailed WebSocket error:")
                    else:
                        logger.error(f"Failed to store script in MongoDB for {message.get('source_name', 'unknown')}")

                    # Publish script generated message
                    await message_broker.publish_script_generated({
                        "script": script,
                        "source_type": message.get("source_type"),
                        "source_name": message.get("source_name"),
                        "collection_id": message.get("collection_id"),
                        "script_id": script.get("_id")  # Include the script ID in the message
                    })
                    logger.info(f"Successfully generated script for {message.get('source_name', 'unknown')}")

                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

            # Start consuming messages in a background task that keeps running
            import asyncio
            # Create a background task that will keep running
            app.state.consumer_task = asyncio.create_task(
                message_broker.consume_data_collected(handle_data_collected)
            )
            logger.info("Started consuming data collected messages in background task")

        except Exception as e:
            logger.error(f"Error during startup: {str(e)}")
            raise
    
    # Register the startup event
    app.add_event_handler("startup", startup_event)
    
    # Execute the startup event directly to ensure it runs
    # This is in addition to the event handler registration
    try:
        logger.info("Manually executing startup event...")
        await startup_event()
        logger.info("Startup event executed successfully")
    except Exception as e:
        logger.error(f"Error manually executing startup event: {str(e)}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("Shutting down Script Generator Service")
        try:
            # Cancel the consumer task if it exists
            if hasattr(app.state, 'consumer_task'):
                logger.info("Cancelling consumer task")
                app.state.consumer_task.cancel()
                try:
                    await app.state.consumer_task
                except asyncio.CancelledError:
                    logger.info("Consumer task cancelled successfully")
            
            # Close the message broker connection
            await message_broker.close()
            logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            raise
    
    # Add exception handlers
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions"""
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )
    
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
        title="Script Generator",
        description="Service for generating video scripts using Gemini API",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware with explicit WebSocket support
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Include routes
    app.include_router(health_routes.router)
    app.include_router(scripting_routes.router, prefix="/api/v1")
    
    # Include WebSocket routes without prefix
    app.include_router(websocket_routes.router)
    
    # Add root endpoint redirect
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "message": "Welcome to Script Generator API",
            "docs_url": "/docs",
            "health_url": "/health"
        }
    
    return app