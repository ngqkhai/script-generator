from fastapi import FastAPI, WebSocket
import uvicorn
from app import create_app
import logging

# Configure logging
logging.basicConfig(
    level="INFO",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the app instance
app = create_app()

# Add a direct WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Additional WebSocket endpoint"""
    logger.info("WebSocket connection request received at /ws")
    
    # Accept the connection
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connection_established",
        "message": "Connected to direct WebSocket endpoint"
    })
    
    # Keep connection open and handle messages
    while True:
        data = await websocket.receive_text()
        logger.info(f"Received message: {data}")
        
        # Echo the message back
        await websocket.send_json({
            "type": "echo",
            "message": data
        })

if __name__ == "__main__":
    logger.info("Starting script generator with direct WebSocket endpoint")
    uvicorn.run(app, host="0.0.0.0", port=8002) 