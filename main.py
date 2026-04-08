from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

from app.core.config import APP_NAME, APP_VERSION
from app.routers.chat import router as chat_router
from app.routers.medication_reminders import router as medication_reminders_router
from app.routers.reminders import router as reminders_router
from app.routers.voice import router as voice_router
from app.services.reminder_service import get_due_reminders, mark_reminder_completed

app = FastAPI(title=APP_NAME, version=APP_VERSION)

scheduler = BackgroundScheduler()

def check_due_reminders():
    try:
        due_reminders = get_due_reminders()
        for reminder in due_reminders:
            print(f"[REMINDER TRIGGERED] Patient {reminder.patient_id}: {reminder.task_description}")
            mark_reminder_completed(str(reminder.id))
    except Exception as e:
        print(f"[Scheduler Error]: {e}")

scheduler.add_job(
    func=check_due_reminders,
    trigger=IntervalTrigger(minutes=1),
    id='reminder_checker',
    name='Check due reminders every minute',
    replace_existing=True
)

scheduler.start()
atexit.register(lambda: scheduler.shutdown())

app.include_router(medication_reminders_router)
app.include_router(chat_router)
app.include_router(reminders_router)
app.include_router(voice_router)


@app.get("/", include_in_schema=False)
def health_check() -> dict:
    return {"status": "ok"}

