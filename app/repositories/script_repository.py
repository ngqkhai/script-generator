import pymongo
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class ScriptRepository:
    """Repository for video script data in MongoDB"""
    
    def __init__(self):
        """Initialize connection to MongoDB"""
        from app.config import settings
        
        try:
            self.client = pymongo.MongoClient(settings.MONGODB_URL)
            self.db = self.client[settings.MONGODB_DB]
            self.collection = self.db["scripts"]
            
            # Create indexes
            self.collection.create_index([("created_at", pymongo.DESCENDING)])
            
            logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")
            logger.info("Created index on created_at field")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def find_one(self, script_id):
        """Find a script by ID
        
        Args:
            script_id: ID of the script
            
        Returns:
            Dict containing script data or None if not found
        """
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(script_id, str) and len(script_id) == 24:
                try:
                    query_id = ObjectId(script_id)
                    result = self.collection.find_one({"_id": query_id})
                    if result:
                        return result
                except:
                    pass
            
            # Try with string ID
            return self.collection.find_one({"_id": script_id})
        except Exception as e:
            logger.error(f"Error finding script {script_id}: {str(e)}")
            return None
    
    def insert_one(self, script):
        """Insert a new script
        
        Args:
            script: Dict containing script data
            
        Returns:
            Boolean indicating success
        """
        try:
            result = self.collection.insert_one(script)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error inserting script: {str(e)}")
            return False
    
    def update_one(self, script_id, update_data):
        """Update a script
        
        Args:
            script_id: ID of the script
            update_data: Dict containing fields to update
            
        Returns:
            Boolean indicating success
        """
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(script_id, str) and len(script_id) == 24:
                try:
                    query_id = ObjectId(script_id)
                    result = self.collection.update_one(
                        {"_id": query_id},
                        {"$set": update_data}
                    )
                    if result.modified_count > 0:
                        return True
                except:
                    pass
            
            # Try with string ID
            result = self.collection.update_one(
                {"_id": script_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating script {script_id}: {str(e)}")
            return False
    
    def delete_one(self, script_id):
        """Delete a script
        
        Args:
            script_id: ID of the script
            
        Returns:
            Boolean indicating success
        """
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(script_id, str) and len(script_id) == 24:
                try:
                    query_id = ObjectId(script_id)
                    result = self.collection.delete_one({"_id": query_id})
                    if result.deleted_count > 0:
                        return True
                except:
                    pass
            
            # Try with string ID
            result = self.collection.delete_one({"_id": script_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting script {script_id}: {str(e)}")
            return False
    
    def find(self, skip=0, limit=10):
        """Find multiple scripts with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of scripts
        """
        try:
            return list(self.collection.find().sort("created_at", -1).skip(skip).limit(limit))
        except Exception as e:
            logger.error(f"Error finding scripts: {str(e)}")
            return []
    
    def count_documents(self, query=None):
        """Count the number of scripts
        
        Args:
            query: Optional query filter
            
        Returns:
            Count of scripts
        """
        try:
            if query:
                return self.collection.count_documents(query)
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Error counting scripts: {str(e)}")
            return 0