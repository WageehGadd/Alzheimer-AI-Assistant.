import os
import tempfile
import io
from pathlib import Path
from typing import Optional

# Try to import audio libraries with fallbacks
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

# Load Whisper model once (lazy loading)
_whisper_model = None

def get_whisper_model():
    """Get or load Whisper model."""
    global _whisper_model
    if _whisper_model is None and WHISPER_AVAILABLE:
        print("Loading Whisper model...")
        _whisper_model = whisper.load_model("base")
        print("Whisper model loaded successfully!")
    return _whisper_model

async def transcribe_audio(audio_file: bytes, file_extension: str = ".wav") -> str:
    """
    Transcribe audio file using OpenAI Whisper.
    
    Args:
        audio_file: Audio file bytes
        file_extension: File extension (.wav, .mp3, etc.)
    
    Returns:
        Transcribed text in Egyptian Arabic
    """
    if not WHISPER_AVAILABLE:
        return "معذرة، نظام تحويل الصوت للنص غير متاح حالياً."
    
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file.write(audio_file)
            temp_file_path = temp_file.name
        
        try:
            # Convert to WAV if needed (Whisper works best with WAV)
            if PYDUB_AVAILABLE and file_extension.lower() != ".wav":
                audio = AudioSegment.from_file(temp_file_path)
                wav_path = temp_file_path.replace(file_extension, ".wav")
                audio.export(wav_path, format="wav")
                temp_file_path = wav_path
            
            # Transcribe using Whisper
            model = get_whisper_model()
            if model is None:
                return "معذرة، نموذج Whisper غير متاح."
            
            result = model.transcribe(temp_file_path, language="ar")
            
            transcribed_text = result["text"].strip()
            
            # Clean and validate the transcription
            if not transcribed_text:
                return "معذرة، مقدرش اسمع حاجة واضحة."
            
            return transcribed_text
            
        finally:
            # Clean up temporary files
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
    """
    Convert text to speech using Edge TTS.
    
    Args:
        text: Text to synthesize (Egyptian Arabic)
        voice: Voice model to use
    
    Returns:
        Audio file bytes (MP3 format)
    """
    if not EDGE_TTS_AVAILABLE:
        raise HTTPException(status_code=500, detail="نظام تحويل النص لصوت غير متاح حالياً.")
    
    try:
        # Initialize Edge TTS
        communicate = edge_tts.Communicate(text, voice)
        
        # Generate audio to bytes directly
        audio_data = await communicate.stream()
        
        # Collect all audio data
        audio_bytes = b""
        async for chunk in audio_data:
            audio_bytes += chunk
        
        return audio_bytes
            
    except Exception as e:
        print(f"[TTS Error]: {e}")
        raise HTTPException(status_code=500, detail=f"فشل في تحويل النص لصوت: {str(e)}")

def get_available_voices():
    """Get list of available Arabic voices."""
    if not EDGE_TTS_AVAILABLE:
        return []
    
    try:
        voices = edge_tts.list_voices()
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
    """
    Validate audio file size and format.
    
    Args:
        audio_bytes: Audio file bytes
        max_size_mb: Maximum file size in MB
    
    Returns:
        True if valid, False otherwise
    """
    # Check file size
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False
    
    # Basic validation - check if it's a valid audio file
    if PYDUB_AVAILABLE:
        try:
            # Try to read with pydub
            with io.BytesIO(audio_bytes) as audio_io:
                AudioSegment.from_file(audio_io)
            return True
        except:
            return False
    else:
        # Fallback: just check if it's not empty
        return len(audio_bytes) > 0

def preprocess_audio(audio_bytes: bytes) -> bytes:
    """
    Preprocess audio for better transcription quality.
    
    Args:
        audio_bytes: Original audio bytes
    
    Returns:
        Processed audio bytes
    """
    if not PYDUB_AVAILABLE:
        return audio_bytes  # Return original if pydub not available
    
    try:
        # Load audio
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Normalize audio (adjust volume)
        audio = audio.normalize()
        
        # Convert to mono (better for STT)
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Set sample rate to 16kHz (optimal for Whisper)
        audio = audio.set_frame_rate(16000)
        
        # Export to bytes
        output = io.BytesIO()
        audio.export(output, format="wav", parameters=["-ar", "16000"])
        return output.getvalue()
        
    except Exception as e:
        print(f"[Audio Preprocessing Error]: {e}")
        return audio_bytes  # Return original if preprocessing fails
