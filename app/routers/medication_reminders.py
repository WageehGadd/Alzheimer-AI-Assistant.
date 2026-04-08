from fastapi import APIRouter

from app.schemas.medication_reminder import MedicationReminderCheckResponse
from app.services.medication_reminders_service import check_medication_reminder


router = APIRouter(prefix="/medication", tags=["Medication Reminders"])


@router.get("/reminders/check", response_model=MedicationReminderCheckResponse)
def check_medication_reminder_endpoint(patient_id: str) -> MedicationReminderCheckResponse:

    status = check_medication_reminder(patient_id=patient_id)

    due_at_iso = status.due_at.isoformat() if status.due_at is not None else None
    if due_at_iso is not None and due_at_iso.endswith("+00:00"):
        due_at_iso = due_at_iso.replace("+00:00", "Z")

    return MedicationReminderCheckResponse(
        patient_id=status.patient_id,
        has_reminder=status.has_reminder,
        next_medication=status.next_medication,
        due_at_iso=due_at_iso,
        message=status.message,
    )

