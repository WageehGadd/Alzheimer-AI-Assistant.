import os
import tempfile
import io
from pathlib import Path
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

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

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not available. OpenAI TTS functionality will be limited.")

from fastapi import HTTPException
from app.core.config import (
    TTS_ENGINE, OPENAI_API_KEY, ELEVENLABS_API_KEY, 
    OPENAI_TTS_VOICE, TTS_AUTO_FALLBACK
)

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

def egyptianize_text(text: str) -> str:
    """Convert Modern Standard Arabic to Egyptian dialect for more natural TTS."""
    replacements = {
        'هل': 'هو',
        'ماذا': 'إيه',
        'لماذا': 'ليه',
        'كيف': 'إزاي',
        'أين': 'فين',
        'متى': 'إمتى',
        'كم': 'قد إيه',
        'من': 'مين',
        'مع': 'مع',
        'إلى': 'لـ',
        'على': 'عـ',
        'في': 'فـ',
        'هذا': 'ده',
        'هذه': 'دي',
        'أولئك': 'دول',
        'الآن': 'النهاردة',
        'اليوم': 'النهاردة',
        'غدا': 'بكرة',
        'أمس': 'امبارح',
        'جيد': 'كويس',
        'ممتاز': 'عظيم',
        'شكرا': 'شكرا',
        'أهلا': 'أهلا',
        'معذرة': 'معذرة',
        'أنا': 'أنا',
        'أنت': 'إنت',
        'هم': 'هم',
        'نحن': 'إحنا'
    }
    
    result = text
    for standard, egyptian in replacements.items():
        result = result.replace(standard, egyptian)
    
    result = result.replace('  ', ' ')
    
    result = result.replace('؟', '؟').replace('.', '،').replace('!', '！')
    
    return result.strip()


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    @abstractmethod
    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        """Synthesize speech from text."""
        pass
    
    @abstractmethod
    async def get_voices(self) -> list[Dict[str, Any]]:
        """Get available voices."""
        pass


class EdgeTTSProvider(TTSProvider):
    """Edge TTS provider implementation."""
    
    def __init__(self):
        self.available = EDGE_TTS_AVAILABLE
    
    async def synthesize(self, text: str, voice: str, **kwargs) -> bytes:
        if not self.available:
            raise HTTPException(status_code=500, detail="Edge TTS not available.")
        
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
            print(f"[Edge TTS Error]: {e}")
            raise HTTPException(status_code=500, detail=f"Edge TTS failed: {str(e)}")
    
    async def get_voices(self) -> list[Dict[str, Any]]:
        if not self.available:
            return []
        
        try:
            voices = await edge_tts.list_voices()
            arabic_voices = [
                {
                    "name": v["ShortName"],
                    "locale": v["Locale"],
                    "gender": v["Gender"],
                    "friendly_name": v["FriendlyName"],
                    "provider": "edge"
                }
                for v in voices 
                if v["Locale"].startswith("ar-")
            ]
            return arabic_voices
        except Exception as e:
            print(f"[Edge Voices Error]: {e}")
            return []


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS provider implementation."""
    
    def __init__(self):
        self.available = OPENAI_AVAILABLE and bool(OPENAI_API_KEY)
        self.client = None
        if self.available:
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    async def synthesize(self, text: str, voice: str = "shimmer", **kwargs) -> bytes:
        if not self.available:
            raise HTTPException(status_code=500, detail="OpenAI TTS not available.")
        
        try:
            egyptian_text = egyptianize_text(text)
            
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice or OPENAI_TTS_VOICE,
                input=egyptian_text,
                response_format="mp3"
            )
            
            audio_bytes = response.content
            return audio_bytes
                
        except Exception as e:
            print(f"[OpenAI TTS Error]: {e}")
            raise HTTPException(status_code=500, detail=f"OpenAI TTS failed: {str(e)}")
    
    async def get_voices(self) -> list[Dict[str, Any]]:
        if not self.available:
            return []
        
        return [
            {
                "name": "alloy",
                "locale": "ar",
                "gender": "neutral",
                "friendly_name": "Alloy (Neutral)",
                "provider": "openai"
            },
            {
                "name": "echo",
                "locale": "ar",
                "gender": "male",
                "friendly_name": "Echo (Male)",
                "provider": "openai"
            },
            {
                "name": "fable",
                "locale": "ar",
                "gender": "neutral",
                "friendly_name": "Fable (Storytelling)",
                "provider": "openai"
            },
            {
                "name": "onyx",
                "locale": "ar",
                "gender": "male",
                "friendly_name": "Onyx (Male)",
                "provider": "openai"
            },
            {
                "name": "nova",
                "locale": "ar",
                "gender": "female",
                "friendly_name": "Nova (Female)",
                "provider": "openai"
            },
            {
                "name": "shimmer",
                "locale": "ar",
                "gender": "female",
                "friendly_name": "Shimmer (Female)",
                "provider": "openai"
            }
        ]


class VoiceService:
    """Modular voice service that manages multiple TTS providers."""
    
    def __init__(self):
        self.providers = {
            "edge": EdgeTTSProvider(),
            "openai": OpenAITTSProvider()
        }
        self.current_engine = TTS_ENGINE
        
    async def synthesize_speech(self, text: str, voice: str = None) -> bytes:
        """Synthesize speech using the configured provider with fallback."""
        
        engines_to_try = [self.current_engine]
        
        if TTS_AUTO_FALLBACK and self.current_engine != "edge":
            engines_to_try.append("edge")
        
        last_error = None
        
        for engine in engines_to_try:
            provider = self.providers.get(engine)
            if provider and provider.available:
                try:
                    if engine == "edge":
                        voice = voice or "ar-EG-SalmaNeural"
                    elif engine == "openai":
                        voice = voice or OPENAI_TTS_VOICE
                    
                    return await provider.synthesize(text, voice)
                    
                except Exception as e:
                    print(f"[{engine.upper()} TTS Error]: {e}")
                    last_error = e
                    continue
        
        if last_error:
            raise HTTPException(status_code=500, detail=f"All TTS providers failed: {str(last_error)}")
        else:
            raise HTTPException(status_code=500, detail="No TTS providers available.")
    
    async def get_available_voices(self) -> list[Dict[str, Any]]:
        """Get available voices from all providers."""
        all_voices = []
        
        for engine_name, provider in self.providers.items():
            if provider.available:
                try:
                    voices = await provider.get_voices()
                    all_voices.extend(voices)
                except Exception as e:
                    print(f"[{engine_name.upper()} Voices Error]: {e}")
        
        return all_voices


voice_service = VoiceService()


async def synthesize_speech(text: str, voice: str = "ar-EG-SalmaNeural") -> bytes:
    """Legacy function for backward compatibility."""
    return await voice_service.synthesize_speech(text, voice)

async def get_available_voices():
    """Legacy function for backward compatibility."""
    return await voice_service.get_available_voices()

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
