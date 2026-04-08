from datetime import datetime
import os

def check_medication_reminder(patient_id: str):
    try:
     
        current_time = datetime.now().strftime("%H:%M")
        
        print(f"[Reminder Service] Checking reminders for Patient {patient_id} at {current_time}")
        
        return {
            "patient_id": patient_id,
            "has_reminder": False,
            "message": "No reminders at this time."
        }
    except Exception as e:
        print(f"[Reminder Service Error]: {e}")
        return None