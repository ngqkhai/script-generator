import uvicorn
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState
import os

# Configure logging
logging.basicConfig(
    level="INFO",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("script_generator.log")
    ]
)

logger = logging.getLogger(__name__)

# Import the app creation function
from app import create_app
from app.utils.websocket_manager import connection_manager

# Create the main application instance
app = create_app()

# Add more robust CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Store active connections by collection_id (for this endpoint only)
active_connections = {}

# Direct WebSocket implementation that works reliably
@app.websocket("/direct-ws")
async def websocket_endpoint(websocket: WebSocket):
    """Direct WebSocket endpoint that is known to work reliably"""
    # Get the collection_id
    collection_id = websocket.query_params.get("collection_id")
    logger.info(f"Direct WebSocket connection request with collection_id: {collection_id}")
    
    if not collection_id:
        logger.warning("WebSocket connection missing collection_id parameter")
        return
    
    # Handle duplicate connections - close existing connection for same collection_id
    if collection_id in active_connections:
        old_connection = active_connections[collection_id]
        if old_connection and old_connection.client_state == WebSocketState.CONNECTED:
            logger.info(f"Closing existing connection for collection_id: {collection_id}")
            try:
                await old_connection.close(code=1000, reason="New connection established")
            except Exception as e:
                logger.error(f"Error closing old connection: {str(e)}")
    
    try:
        # Accept the connection
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        # Store the connection in both registries
        active_connections[collection_id] = websocket
        
        # IMPORTANT: Also register with the connection_manager so notifications work
        await connection_manager.connect(websocket, collection_id)
        logger.info(f"Registered connection with connection_manager for collection_id: {collection_id}")
        
        # Print debug info about active connections
        logger.info(f"Active /direct-ws connections: {list(active_connections.keys())}")
        logger.info(f"Connection manager collection connections: {list(connection_manager.collection_connections.keys())}")
        
        # Send immediate connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to script generator WebSocket",
            "collection_id": collection_id
        })
        logger.info("Sent connection confirmation")
        
        # Keep connection alive by handling incoming messages and sending periodic pings
        while True:
            try:
                # Wait for messages with a timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                logger.info(f"Received message: {data}")
                
                # Echo the message back
                await websocket.send_json({
                    "type": "echo",
                    "message": data
                })
            except asyncio.TimeoutError:
                # Send a ping if no message received for 30 seconds
                if websocket.client_state == WebSocketState.CONNECTED:
                    logger.info("Sending ping to keep connection alive")
                    await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for collection_id: {collection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Clean up connection from registries when it closes
        if collection_id in active_connections and active_connections[collection_id] == websocket:
            logger.info(f"Removing connection from /direct-ws registry for collection_id: {collection_id}")
            del active_connections[collection_id]
        
        # Also disconnect from the connection manager
        connection_manager.disconnect(websocket, collection_id)
        logger.info(f"Disconnected from connection_manager for collection_id: {collection_id}")

# Manual trigger of startup event for debugging
@app.on_event("startup")
async def debug_startup():
    logger.info("MANUAL STARTUP EVENT TRIGGERED - This should appear in logs")

if __name__ == "__main__":
    logger.info("Starting script generator service")
    # Configure uvicorn with websocket-specific settings
    uvicorn.run(
        app,  # Use the app instance directly
        host="0.0.0.0", 
        port=8002,
        log_level="info",
        reload=False,
        timeout_keep_alive=120,  # Keep connections alive longer (2 minutes)
        headers=[
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
            ("Access-Control-Allow-Credentials", "true"),
        ],
        ws_ping_interval=30.0,  # Send ping frames every 30 seconds
        ws_ping_timeout=60.0,   # Wait 60 seconds for pong response before closing
        ws_max_size=10 * 1024 * 1024,  # 10MB limit for WebSocket messages
    )