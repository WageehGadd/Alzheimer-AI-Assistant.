from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class ReminderRequest(BaseModel):
    patient_id: str = Field(...)
    message: str = Field(...)
    
class ReminderResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    patient_id: str
    task_description: str
    remind_time: datetime
    is_completed: bool = False
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

class ReminderCreate(BaseModel):
    patient_id: str
    task_description: str
    remind_time: datetime
