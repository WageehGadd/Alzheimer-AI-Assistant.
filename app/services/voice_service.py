import os
import tempfile
import io
from pathlib import Path
from typing import Optional

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: OpenAI Whisper not available. STT functionality will be limited.")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("Warning: Edge TTS not available. TTS functionality will be limited.")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Warning: Pydub not available. Audio processing will be limited.")

from fastapi import HTTPException

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None and WHISPER_AVAILABLE:
        print("Loading Whisper model...")
        _whisper_model = whisper.load_model("base")
        print("Whisper model loaded successfully!")
    return _whisper_model

async def transcribe_audio(audio_file: bytes, file_extension: str = ".wav") -> str:
    if not WHISPER_AVAILABLE:
        return "معذرة، نظام تحويل الصوت للنص غير متاح حالياً."
    
    try:
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file.write(audio_file)
            temp_file_path = temp_file.name
        
        try:
            if PYDUB_AVAILABLE and file_extension.lower() != ".wav":
                audio = AudioSegment.from_file(temp_file_path)
                wav_path = temp_file_path.replace(file_extension, ".wav")
                audio.export(wav_path, format="wav")
                temp_file_path = wav_path
            
            model = get_whisper_model()
            if model is None:
                return "معذرة، نموذج Whisper غير متاح."
            
            result = model.transcribe(temp_file_path, language="ar")
            
            transcribed_text = result["text"].strip()
            
            if not transcribed_text:
                return "معذرة، مقدرش اسمع حاجة واضحة."
            
            return transcribed_text
            
        finally:
            try:
                os.unlink(temp_file_path)
                if PYDUB_AVAILABLE and file_extension.lower() != ".wav" and os.path.exists(temp_file_path.replace(file_extension, ".wav")):
                    os.unlink(temp_file_path.replace(file_extension, ".wav"))
            except:
                pass
                
    except Exception as e:
        print(f"[STT Error]: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في تحويل الصوت لنص: {str(e)}")

async def synthesize_speech(text: str, voice: str = "ar-EG-SalmaNeural") -> bytes:
    if not EDGE_TTS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Voice to text system not available.")
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
        
        await communicate.save(temp_path)
        
        with open(temp_path, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(temp_path)
        
        return audio_bytes
            
    except Exception as e:
        print(f"[TTS Error]: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to convert text to speech: {str(e)}")

async def get_available_voices():
    if not EDGE_TTS_AVAILABLE:
        return []
    
    try:
        voices = await edge_tts.list_voices()
        arabic_voices = [
            {
                "name": v["ShortName"],
                "locale": v["Locale"],
                "gender": v["Gender"],
                "friendly_name": v["FriendlyName"]
            }
            for v in voices 
            if v["Locale"].startswith("ar-")
        ]
        return arabic_voices
    except Exception as e:
        print(f"[Voice List Error]: {e}")
        return []

def validate_audio_file(audio_bytes: bytes, max_size_mb: int = 25) -> bool:
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False
    
    if PYDUB_AVAILABLE:
        try:
            with io.BytesIO(audio_bytes) as audio_io:
                AudioSegment.from_file(audio_io)
            return True
        except:
            return False
    else:
        return len(audio_bytes) > 0

def preprocess_audio(audio_bytes: bytes) -> bytes:
    if not PYDUB_AVAILABLE:
        return audio_bytes
    
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        audio = audio.normalize()
        
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        audio = audio.set_frame_rate(16000)
        
        output = io.BytesIO()
        audio.export(output, format="wav", parameters=["-ar", "16000"])
        return output.getvalue()
        
    except Exception as e:
        print(f"[Audio Preprocessing Error]: {e}")
        return audio_bytes
