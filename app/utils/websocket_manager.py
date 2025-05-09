import logging
from typing import Dict, List, Optional, Any
from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections to clients.
    """
    def __init__(self):
        # Track all active connections
        self.active_connections: List[WebSocket] = []
        # Map collection_ids to connections for targeted messages
        self.collection_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, collection_id: Optional[str] = None):
        """
        Register a WebSocket connection and add it to the active connections.
        Note: The connection should already be accepted by the route handler.
        
        Args:
            websocket: The WebSocket connection
            collection_id: Optional collection ID to associate with this connection
        """
        # Add to active connections if not already present
        if websocket not in self.active_connections:
            self.active_connections.append(websocket)
            logger.info(f"New WebSocket connection added to manager. Total connections: {len(self.active_connections)}")
        
        # If a collection_id is provided, associate this connection with it
        if collection_id:
            if collection_id not in self.collection_connections:
                self.collection_connections[collection_id] = []
            
            if websocket not in self.collection_connections[collection_id]:
                self.collection_connections[collection_id].append(websocket)
                logger.info(f"WebSocket connection associated with collection_id: {collection_id}")
                logger.info(f"Now have {len(self.collection_connections[collection_id])} connection(s) for collection_id: {collection_id}")
            
            # Log all current collections
            logger.info(f"All active collection IDs: {list(self.collection_connections.keys())}")
    
    def disconnect(self, websocket: WebSocket, collection_id: Optional[str] = None):
        """
        Remove a WebSocket connection from the active connections.
        
        Args:
            websocket: The WebSocket connection to remove
            collection_id: Optional collection ID associated with this connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket connection removed. Remaining connections: {len(self.active_connections)}")
        
        # Remove from collection mapping if present
        for coll_id, connections in list(self.collection_connections.items()):
            if websocket in connections:
                connections.remove(websocket)
                logger.info(f"WebSocket connection removed from collection_id: {coll_id}")
                
                # Clean up empty lists
                if not connections:
                    del self.collection_connections[coll_id]
                    logger.info(f"Removed empty collection mapping for collection_id: {coll_id}")
                else:
                    logger.info(f"Still have {len(connections)} connection(s) for collection_id: {coll_id}")
    
    async def send_to_collection(self, collection_id: str, message: Dict[str, Any]):
        """
        Send a message to all clients associated with a specific collection_id.
        
        Args:
            collection_id: The collection ID to target
            message: The message to send
        """
        if collection_id not in self.collection_connections:
            logger.warning(f"No active connections for collection_id: {collection_id}")
            logger.info(f"Available collection IDs: {list(self.collection_connections.keys())}")
            return
            
        disconnected = []
        successful_sends = 0
        
        logger.info(f"Attempting to send message to {len(self.collection_connections[collection_id])} clients for collection {collection_id}")
        
        for connection in self.collection_connections[collection_id]:
            try:
                # Check if the connection is still open before sending
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                    successful_sends += 1
                    logger.info(f"Successfully sent message to client for collection {collection_id}")
                else:
                    logger.warning(f"Connection for collection {collection_id} is not in CONNECTED state")
                    disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending message to client for collection {collection_id}: {str(e)}")
                logger.exception("Detailed error:")
                disconnected.append(connection)
        
        # Clean up any disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
            
        if successful_sends > 0:
            logger.info(f"Successfully sent message to {successful_sends} clients for collection {collection_id}")
        else:
            logger.warning(f"Failed to send message to any clients for collection {collection_id}")
    
    def debug_dump_connections(self):
        """
        Dump all connection information for debugging purposes.
        """
        logger.info("==== CONNECTION MANAGER DEBUG DUMP ====")
        logger.info(f"Total active connections: {len(self.active_connections)}")
        logger.info(f"Total collection mappings: {len(self.collection_connections)}")
        
        for coll_id, connections in self.collection_connections.items():
            logger.info(f"Collection {coll_id}: {len(connections)} connection(s)")
            
            for i, conn in enumerate(connections):
                state = "UNKNOWN"
                try:
                    if conn.client_state == WebSocketState.CONNECTED:
                        state = "CONNECTED"
                    elif conn.client_state == WebSocketState.DISCONNECTED:
                        state = "DISCONNECTED"
                    elif conn.client_state == WebSocketState.CONNECTING:
                        state = "CONNECTING"
                except Exception:
                    state = "ERROR-CHECKING"
                    
                logger.info(f"  Connection {i+1}: State = {state}")
                
        logger.info("==== END DEBUG DUMP ====")

# Create a singleton instance
connection_manager = ConnectionManager() 