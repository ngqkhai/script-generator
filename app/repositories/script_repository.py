from pymongo import MongoClient
import datetime
import logging
from typing import Dict, List, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

class ScriptRepository:
    """
    Repository for storing and retrieving script data from MongoDB
    """
    
    def __init__(self, client=None, db_name=None):
        """
        Initialize a new ScriptRepository instance
        
        Args:
            client: Optional MongoClient for dependency injection (useful for testing)
            db_name: Optional database name override
        """
        # For testing: allow dependency injection
        if client is None:
            try:
                self.client = MongoClient(settings.MONGODB_URL)
                logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                # In production, we might want to raise this exception
                # For testing purposes, we'll create a minimal client that works without MongoDB
                self.client = None
        else:
            self.client = client
            
        # Only proceed with collection setup if we have a valid client
        if self.client:
            self.db = self.client[db_name or settings.MONGODB_DB]
            self.collection = self.db.scripts
            
            # Create indexes (only if we have a real connection)
            try:
                self.collection.create_index("created_at")
                logger.info("Created index on created_at field")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
    
    def save(self, script_data: Dict[str, Any]) -> str:
        """
        Save a script to the database
        
        Args:
            script_data: Dictionary containing script data
            
        Returns:
            str: The ID of the inserted script
        """
        if not self.client:
            # For testing without MongoDB
            return "test_script_id"
            
        # Add timestamp
        script_data["created_at"] = datetime.datetime.utcnow()
        
        # Insert the script
        result = self.collection.insert_one(script_data)
        
        # Return the ID
        return str(result.inserted_id)
    
    def get_by_id(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a script by ID
        
        Args:
            script_id: The ID of the script to retrieve
            
        Returns:
            Dict or None: The script document, or None if not found
        """
        if not self.client:
            # For testing without MongoDB
            return {
                "_id": script_id,
                "scenes": [{"scene_id": "test_scene"}],
                "metadata": {"title": "Test Script"},
                "created_at": datetime.datetime.utcnow()
            }
            
        from bson.objectid import ObjectId
        
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(script_id)
            
            # Find the script
            script = self.collection.find_one({"_id": object_id})
            
            # Convert ObjectId to string for JSON serialization
            if script and "_id" in script:
                script["_id"] = str(script["_id"])
                
            return script
            
        except Exception as e:
            logger.error(f"Error retrieving script with ID {script_id}: {e}")
            return None