import os
from datetime import datetime, timedelta
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
from app.schemas.reminder import ReminderResponse, ReminderCreate

# --- DB CONFIG ---
_MONGO_URI = os.getenv("MONGO_URI")
_DB_NAME = "alzheimer_app"
_COLLECTION_NAME = "reminders"

def get_mongo_client():
    """Get MongoDB client connection."""
    return MongoClient(_MONGO_URI)

def get_reminders_collection():
    """Get reminders collection."""
    client = get_mongo_client()
    db = client[_DB_NAME]
    return db[_COLLECTION_NAME]

def create_reminder(reminder_data: ReminderCreate) -> ReminderResponse:
    """Create a new reminder in MongoDB."""
    collection = get_reminders_collection()
    
    reminder_doc = {
        "patient_id": reminder_data.patient_id,
        "task_description": reminder_data.task_description,
        "remind_time": reminder_data.remind_time,
        "is_completed": False,
        "created_at": datetime.utcnow()
    }
    
    result = collection.insert_one(reminder_doc)
    
    # Convert ObjectId to string for response
    reminder_doc["_id"] = str(result.inserted_id)
    
    return ReminderResponse(**reminder_doc)

def get_pending_reminders(patient_id: str) -> List[ReminderResponse]:
    """Get all pending reminders for a patient."""
    collection = get_reminders_collection()
    
    reminders = collection.find({
        "patient_id": patient_id,
        "is_completed": False,
        "remind_time": {"$gte": datetime.utcnow()}
    }).sort("remind_time", 1)
    
    return [ReminderResponse(**reminder) for reminder in reminders]

def get_all_reminders(patient_id: str) -> List[ReminderResponse]:
    """Get all reminders for a patient (including completed)."""
    collection = get_reminders_collection()
    
    reminders = collection.find({
        "patient_id": patient_id
    }).sort("remind_time", 1)
    
    return [ReminderResponse(**reminder) for reminder in reminders]

def mark_reminder_completed(reminder_id: str) -> bool:
    """Mark a reminder as completed."""
    collection = get_reminders_collection()
    
    try:
        object_id = ObjectId(reminder_id)
        result = collection.update_one(
            {"_id": object_id},
            {"$set": {"is_completed": True}}
        )
        return result.modified_count > 0
    except:
        return False

def get_due_reminders() -> List[ReminderResponse]:
    """Get all reminders that are due (time has passed and not completed)."""
    collection = get_reminders_collection()
    
    reminders = collection.find({
        "is_completed": False,
        "remind_time": {"$lte": datetime.utcnow()}
    }).sort("remind_time", 1)
    
    return [ReminderResponse(**reminder) for reminder in reminders]

def delete_reminder(reminder_id: str) -> bool:
    """Delete a reminder."""
    collection = get_reminders_collection()
    
    try:
        object_id = ObjectId(reminder_id)
        result = collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
    except:
        return False
