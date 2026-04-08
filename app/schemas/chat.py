from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    patient_id: str
    message: str
    raw_ocr_text: Optional[str] = None
    include_audio_response: Optional[bool] = False

class ChatMessageResponse(BaseModel):
    patient_id: str
    response_message: str
    audio_response: Optional[str] = None