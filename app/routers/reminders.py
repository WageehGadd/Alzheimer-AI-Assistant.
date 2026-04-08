from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.reminder import ReminderResponse, ReminderRequest
from app.services.reminder_service import (
    create_reminder, 
    get_pending_reminders, 
    get_all_reminders,
    mark_reminder_completed,
    delete_reminder,
    ReminderCreate
)
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.post("/reminders", response_model=ReminderResponse)
async def create_new_reminder(request: ReminderRequest):
    """Create a new reminder for a patient."""
    try:
        # Use LLM to extract task and time from natural language
        from app.services.chat_agent import llm
        import json
        
        extraction_prompt = f"""
        استخرج من الجملة دي: المهمة والوقت.
        الجملة: "{request.message}"
        
        رجع كمان JSON بالصيغة دي:
        {{"task": "المهمة المطلوبة", "time": "الوقت بالصيغة 24 ساعة"}}
        
        لو الوقت نسبي (مثل "كمان ساعة" أو "الساعة 9 بالليل")، حوّله لوقت مطلق بناءً على الوقت الحالي: {datetime.now().strftime('%H:%M')}
        """
        
        extraction_response = llm.invoke(extraction_prompt)
        
        # Parse the LLM response to get task and time
        try:
            extracted_data = json.loads(extraction_response.content)
            task = extracted_data.get("task", request.message)
            time_str = extracted_data.get("time", "")
        except:
            # Fallback: simple parsing
            task = request.message
            time_str = datetime.now().strftime('%H:%M')
        
        # Convert time string to datetime
        if ":" in time_str:
            today = datetime.now().date()
            remind_time = datetime.combine(today, datetime.strptime(time_str, '%H:%M').time())
        else:
            # Default to 1 hour from now
            remind_time = datetime.now() + timedelta(hours=1)
        
        # Create reminder in database
        reminder_data = ReminderCreate(
            patient_id=request.patient_id,
            task_description=task,
            remind_time=remind_time
        )
        
        created_reminder = create_reminder(reminder_data)
        
        # Ensure the response has the correct ID format
        response_dict = created_reminder.dict()
        response_dict['id'] = str(created_reminder.id) if created_reminder.id else None
        
        return ReminderResponse(**response_dict)
        
    except Exception as e:
        print(f"[Reminder Creation Error]: {e}")
        raise HTTPException(status_code=500, detail="Failed to create reminder")

@router.get("/reminders/{patient_id}", response_model=List[ReminderResponse])
async def get_reminders_for_patient(patient_id: str):
    """Get all pending reminders for a patient."""
    try:
        reminders = get_pending_reminders(patient_id)
        return reminders
    except Exception as e:
        print(f"[Get Reminders Error]: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reminders")

@router.get("/reminders/{patient_id}/all", response_model=List[ReminderResponse])
async def get_all_reminders_for_patient(patient_id: str):
    """Get all reminders (including completed) for a patient."""
    try:
        reminders = get_all_reminders(patient_id)
        return reminders
    except Exception as e:
        print(f"[Get All Reminders Error]: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reminders")

@router.put("/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: str):
    """Mark a reminder as completed."""
    try:
        success = mark_reminder_completed(reminder_id)
        if success:
            return {"status": "success", "message": "Reminder marked as completed"}
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")
    except Exception as e:
        print(f"[Complete Reminder Error]: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete reminder")

@router.delete("/reminders/{reminder_id}")
async def delete_reminder_endpoint(reminder_id: str):
    """Delete a reminder."""
    try:
        success = delete_reminder(reminder_id)
        if success:
            return {"status": "success", "message": "Reminder deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Reminder not found")
    except Exception as e:
        print(f"[Delete Reminder Error]: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete reminder")
