from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MedicationReminderStatus:
    patient_id: str
    has_reminder: bool
    next_medication: Optional[str]
    due_at: Optional[datetime]
    message: str

