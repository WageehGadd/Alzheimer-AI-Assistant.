from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import base64
from typing import Optional

from app.services.voice_service import (
    transcribe_audio, 
    synthesize_speech, 
    get_available_voices,
    validate_audio_file,
    preprocess_audio
)

router = APIRouter()

@router.post("/voice-to-text")
async def voice_to_text(audio_file: UploadFile = File(...)):
    try:
        audio_bytes = await audio_file.read()
        
        if not validate_audio_file(audio_bytes):
            raise HTTPException(
                status_code=400, 
                detail="ملف الصوت غير صالح أو كبير جداً (أقصى حجم 25 ميجابايت)"
            )
        
        file_extension = ""
        if audio_file.filename:
            file_extension = Path(audio_file.filename).suffix.lower()
        
        processed_audio = preprocess_audio(audio_bytes)
        
        transcription = await transcribe_audio(processed_audio, file_extension)
        
        return {
            "transcription": transcription,
            "filename": audio_file.filename,
            "size_mb": len(audio_bytes) / (1024 * 1024)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Voice-to-Text API Error]: {e}")
        raise HTTPException(status_code=500, detail="فشل في تحويل الصوت لنص")

@router.get("/text-to-speech")
async def text_to_speech(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query("ar-EG-SalmaNeural", description="Voice model"),
    return_base64: bool = Query(False, description="Return base64 encoded audio")
):
    try:
        if not text.strip():
            raise HTTPException(
                status_code=400, 
                detail="النص لا يمكن أن يكون فارغاً"
            )
        
        audio_bytes = await synthesize_speech(text, voice)
        
        if return_base64:
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return {
                "audio_base64": audio_base64,
                "voice": voice,
                "text": text
            }
        else:
            return StreamingResponse(
                io.BytesIO(audio_bytes),
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": f"attachment; filename=speech.mp3"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Text-to-Speech API Error]: {e}")
        raise HTTPException(status_code=500, detail="فشل في تحويل النص لصوت")

@router.get("/voices")
async def list_voices():
    try:
        voices = await get_available_voices()
        return {
            "voices": voices,
            "total": len(voices)
        }
    except Exception as e:
        print(f"[Voices API Error]: {e}")
        raise HTTPException(status_code=500, detail="فشل في جلب قائمة الأصوات")

@router.post("/test-voice")
async def test_voice_system(
    audio_file: Optional[UploadFile] = File(None),
    test_text: str = Query("مرحباً، كيف يمكنني مساعدتك اليوم؟", description="Test text for TTS")
):
    try:
        result = {"test_results": {}}
        
        if test_text:
            tts_audio = await synthesize_speech(test_text)
            tts_base64 = base64.b64encode(tts_audio).decode('utf-8')
            result["test_results"]["tts"] = {
                "success": True,
                "text": test_text,
                "audio_base64": tts_base64[:100] + "..."
            }
        
        if audio_file:
            audio_bytes = await audio_file.read()
            if validate_audio_file(audio_bytes):
                transcription = await transcribe_audio(audio_bytes, Path(audio_file.filename).suffix)
                result["test_results"]["stt"] = {
                    "success": True,
                    "filename": audio_file.filename,
                    "transcription": transcription
                }
            else:
                result["test_results"]["stt"] = {
                    "success": False,
                    "error": "ملف الصوت غير صالح"
                }
        
        return result
        
    except Exception as e:
        print(f"[Voice Test API Error]: {e}")
        raise HTTPException(status_code=500, detail="فشل في اختبار نظام الصوت")
