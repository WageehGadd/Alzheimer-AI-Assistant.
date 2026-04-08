import os
import shutil
import base64
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.chat_agent import (
    generate_chat_response,
    search_medicine_online,
    get_patient_history,
    medicine_ocr_analysis,
)
from app.services.ocr_service import extract_text_from_image
from app.services.voice_service import transcribe_audio, synthesize_speech
from app.schemas.chat import ChatRequest, ChatMessageResponse

router = APIRouter()


@router.post("/chat", response_model=ChatMessageResponse)
async def chat(request: ChatRequest):
    try:
        if request.raw_ocr_text:
            message_with_ocr = f"المريض كتب: {request.message}\n\nنص OCR من صورة الدواء: {request.raw_ocr_text}"
            response = generate_chat_response(request.patient_id, message_with_ocr)
        else:
            response = generate_chat_response(request.patient_id, request.message)
        
        if request.include_audio_response and response.response_message:
            try:
                audio_bytes = await synthesize_speech(response.response_message)
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                response.audio_response = audio_base64
            except Exception as e:
                print(f"[TTS Error in chat]: {e}")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/voice")
async def chat_with_voice(
    patient_id: str = Form(...),
    audio_file: UploadFile = File(...),
    include_audio_response: bool = Form(True)
):
    try:
        audio_bytes = await audio_file.read()
        
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="ملف الصوت فارغ")
        
        file_extension = ""
        if audio_file.filename:
            file_extension = Path(audio_file.filename).suffix.lower()
        
        transcription = await transcribe_audio(audio_bytes, file_extension)
        
        response = generate_chat_response(patient_id, transcription)
        
        if include_audio_response and response.response_message:
            try:
                audio_bytes = await synthesize_speech(response.response_message)
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                response.audio_response = audio_base64
            except Exception as e:
                print(f"[TTS Error in voice chat]: {e}")
        
        return {
            "transcription": transcription,
            "response": response.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Voice Chat Error]: {e}")
        raise HTTPException(status_code=500, detail="فشل في معالجة المحادثة الصوتية")


@router.post("/scan-medicine")
async def scan_medicine(
    patient_id: str = Form(...),
    file: UploadFile = File(...),
):
    temp_file = Path(f"temp_{file.filename}")
    try:
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        raw_text = extract_text_from_image(str(temp_file))

        if not raw_text or len(raw_text.strip()) < 2:
            return {"status": "warning", "message": "Image too blurry."}

        ai_analysis = generate_chat_response(
            patient_id, 
            f"حلل نص الدواء ده: {raw_text}"
        )

        return {
            "status": "success",
            "data": {
                "extracted_text": raw_text,
                "ai_response": ai_analysis.response_message,
            },
        }
    except Exception as e:
        print(f"[Scan Error]: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if temp_file.exists():
            temp_file.unlink()


@router.get("/chat/history/{patient_id}")
async def get_chat_history(patient_id: str):
    try:
        messages = get_patient_history(patient_id)
        return messages
    except Exception as e:
        print(f"[History Error]: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch history.")