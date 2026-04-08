from pydantic import BaseModel
from typing import Optional

# Data coming from the Mobile App / Frontend
class ChatRequest(BaseModel):
    patient_id: str
    message: str
    raw_ocr_text: Optional[str] = None  # Optional OCR text from medicine scanning
    include_audio_response: Optional[bool] = False  # Whether to include TTS audio in response

# Data going back to the Mobile App / Frontend
class ChatMessageResponse(BaseModel):
    patient_id: str
    response_message: str
    audio_response: Optional[str] = None  # Base64 encoded audio response