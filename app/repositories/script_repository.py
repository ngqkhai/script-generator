from typing import List, Dict, Any, Optional
import pymongo
from bson.objectid import ObjectId
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class ScriptRepository:
    """MongoDB repository using pymongo"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScriptRepository, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        """Initialize the MongoDB connection"""
        self.client = pymongo.MongoClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB]
        self.collection = self.db["scripts"]
        
        # Create indexes
        self.collection.create_index("created_at")
        self.collection.create_index([("metadata.title", pymongo.TEXT)])
        
        logger.info("MongoDB script repository initialized")
        self._initialized = True
    
    def save(self, data: Dict[str, Any]) -> str:
        """Save a script to MongoDB
        
        Args:
            data: Script data to save
            
        Returns:
            ID of the saved document
        """
        try:
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
                
            result = self.collection.insert_one(data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving script to MongoDB: {str(e)}")
            raise
    
    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find a script by ID
        
        Args:
            id: Script ID
            
        Returns:
            Script document or None if not found
        """
        try:
            if not ObjectId.is_valid(id):
                return None
                
            document = self.collection.find_one({"_id": ObjectId(id)})
            if document:
                document["id"] = str(document["_id"])
                del document["_id"]
                return document
            return None
        except Exception as e:
            logger.error(f"Error finding script by ID: {str(e)}")
            return None
    
    def update(self, id: str, data: Dict[str, Any]) -> bool:
        """Update a script by ID
        
        Args:
            id: Script ID
            data: Updated script data
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if "updated_at" not in data:
                data["updated_at"] = datetime.utcnow()
                
            if not ObjectId.is_valid(id):
                return False
                
            update_result = self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
            
            return update_result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating script: {str(e)}")
            return False
    
    def delete(self, id: str) -> bool:
        """Delete a script by ID
        
        Args:
            id: Script ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if not ObjectId.is_valid(id):
                return False
                
            result = self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting script: {str(e)}")
            return False
    
    def list(self, filter: Dict[str, Any], limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """List scripts with filtering and pagination
        
        Args:
            filter: Filter criteria
            limit: Maximum number of results to return
            skip: Number of results to skip
            
        Returns:
            List of script documents
        """
        try:
            cursor = self.collection.find(filter).sort("created_at", -1).skip(skip).limit(limit)
            scripts = []
            
            for document in cursor:
                document["id"] = str(document["_id"])
                del document["_id"]
                scripts.append(document)
                
            return scripts
        except Exception as e:
            logger.error(f"Error listing scripts: {str(e)}")
            return []