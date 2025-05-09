from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
import logging
from typing import Optional
import json
import asyncio
from starlette.websockets import WebSocketState

from app.utils.websocket_manager import connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    collection_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for script generation notifications.
    
    Args:
        websocket: The WebSocket connection
        collection_id: Optional collection ID to filter notifications
    """
    logger.info(f"WebSocket connection attempt with collection_id: {collection_id}")
    
    try:
        # Accept the connection directly - don't do any other processing before this
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for collection_id: {collection_id}")
        
        # Simple immediate response to confirm connection works
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to script generator WebSocket",
            "collection_id": collection_id
        })
        logger.info(f"Sent initial confirmation message for collection_id: {collection_id}")
        
        # Now register with the connection manager
        await connection_manager.connect(websocket, collection_id)
        
        # Log connection registration status
        if collection_id:
            if collection_id in connection_manager.collection_connections:
                conn_count = len(connection_manager.collection_connections.get(collection_id, []))
                logger.info(f"Connection registered. Now have {conn_count} connections for collection_id: {collection_id}")
                logger.info(f"All registered collections: {list(connection_manager.collection_connections.keys())}")
            else:
                logger.warning(f"Failed to register connection for collection_id: {collection_id}")
        
        # Keep the connection alive and handle any incoming messages
        while True:
            # Wait for messages from the client with a timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                logger.info(f"Received message from client: {data[:100]}...")
                
                try:
                    # Parse the message as JSON
                    message = json.loads(data)
                    
                    # Simple echo response
                    await websocket.send_json({
                        "type": "echo",
                        "message": message
                    })
                    
                except json.JSONDecodeError:
                    # Handle non-JSON messages
                    logger.warning(f"Received invalid JSON message: {data}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON message"
                    })
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {str(e)}")
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Error processing message: {str(e)}"
                        })
            
            # Send a ping message every 60 seconds if no messages received
            except asyncio.TimeoutError:
                if websocket.client_state == WebSocketState.CONNECTED:
                    logger.debug(f"Sending keepalive ping for collection_id: {collection_id}")
                    await websocket.send_json({"type": "ping"})
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for collection_id: {collection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Always clean up the connection
        connection_manager.disconnect(websocket, collection_id)
        logger.info(f"Connection cleanup completed for collection_id: {collection_id}")
        
        # Log connection status after cleanup
        if collection_id and collection_id in connection_manager.collection_connections:
            conn_count = len(connection_manager.collection_connections.get(collection_id, []))
            logger.info(f"After cleanup: {conn_count} connections remain for collection_id: {collection_id}")
        else:
            logger.info(f"Collection ID {collection_id} no longer has any connections") 