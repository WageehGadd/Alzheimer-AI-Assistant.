from typing import Optional

from pydantic import BaseModel, Field


class MedicationReminderCheckResponse(BaseModel):
    patient_id: str = Field(..., min_length=1)
    has_reminder: bool
    next_medication: Optional[str] = None
    due_at_iso: Optional[str] = None
    message: str

