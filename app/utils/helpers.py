from datetime import datetime
import json

def json_serializable(obj):
    """
    Convert an object to a JSON serializable format
    Handles datetime objects by converting them to ISO format strings
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable") 