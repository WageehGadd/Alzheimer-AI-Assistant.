# Advanced Voice Engine Upgrade Documentation

## Overview
The voice service has been upgraded with a modular architecture supporting multiple TTS providers with automatic fallback capabilities and Egyptian Arabic dialect preprocessing.

## Features

### 1. Modular TTS Provider Architecture
- **Edge TTS**: Local, free option (default)
- **OpenAI TTS**: Premium quality with natural Egyptian Arabic support
- **ElevenLabs**: Framework ready for future implementation

### 2. Egyptian Arabic Dialect Preprocessing
Automatic conversion of Modern Standard Arabic to Egyptian dialect for more natural speech:
- "How" -> "How"
- "How are you" -> "How are you"
- "Thank you" -> "Thank you"
- Proper spacing and punctuation for natural breathing pauses

### 3. Automatic Fallback System
If the primary TTS provider fails, automatically falls back to Edge TTS to ensure service continuity.

## Configuration

### Environment Variables (.env)
```bash
# TTS Engine Selection
TTS_ENGINE=edge                    # Options: edge, openai, elevenlabs

# OpenAI TTS Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_TTS_VOICE=shimmer           # Options: alloy, echo, fable, onyx, nova, shimmer

# Fallback Configuration
TTS_AUTO_FALLBACK=true             # Enable automatic fallback to Edge TTS
```

### Voice Options

#### OpenAI TTS Voices
- **alloy**: Neutral, balanced voice
- **echo**: Male voice
- **fable**: Storytelling style
- **onyx**: Male voice, deep
- **nova**: Female voice
- **shimmer**: Female voice, warm (recommended for Arabic)

#### Edge TTS Voices
- **ar-EG-SalmaNeural**: Egyptian Arabic female
- **ar-EG-ShakirNeural**: Egyptian Arabic male

## Installation

1. Install the OpenAI library:
```bash
pip install openai
```

2. Update your .env file with OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
TTS_ENGINE=openai
```

## Usage Examples

### Basic Usage (Backward Compatible)
```python
from app.services.voice_service import synthesize_speech

# Uses configured TTS engine with automatic fallback
audio_bytes = await synthesize_speech("How are you today?")
```

### Advanced Usage
```python
from app.services.voice_service import voice_service

# Direct access to the modular service
audio_bytes = await voice_service.synthesize_speech(
    text="How are you today?",
    voice="shimmer"  # OpenAI voice
)

# Get all available voices
voices = await voice_service.get_available_voices()
```

### Egyptian Dialect Preprocessing
```python
from app.services.voice_service import egyptianize_text

egyptian_text = egyptianize_text("How are you today?")
print(egyptian_text)  # Output: "How are you today?"
```

## Architecture

### Class Structure
```
TTSProvider (Abstract Base Class)
    |
    |-- EdgeTTSProvider
    |-- OpenAITTSProvider
    |-- ElevenLabsTTSProvider (future)

VoiceService (Main orchestrator)
    |
    |-- Manages multiple providers
    |-- Handles fallback logic
    |-- Applies Egyptian dialect preprocessing
```

### Error Handling
- Provider availability checks
- Graceful fallback to Edge TTS
- Detailed error logging
- HTTP exception handling

## Migration Guide

### From Old System
The upgrade maintains full backward compatibility. Existing code will continue to work:

```python
# This still works exactly as before
audio_bytes = await synthesize_speech("Hello", "ar-EG-SalmaNeural")
```

### To Use New Features
```python
# Enable OpenAI TTS with Egyptian dialect preprocessing
# Set TTS_ENGINE=openai in .env

# The system will automatically:
# 1. Convert text to Egyptian dialect
# 2. Use OpenAI TTS with shimmer voice
# 3. Fallback to Edge TTS if OpenAI fails
```

## Benefits

1. **Higher Quality Voice**: OpenAI TTS provides more natural, human-like speech
2. **Egyptian Dialect**: Automatic preprocessing for authentic Egyptian Arabic
3. **Reliability**: Automatic fallback ensures service never goes down
4. **Flexibility**: Easy switching between providers
5. **Future-Ready**: Framework supports adding more providers

## Troubleshooting

### OpenAI TTS Not Working
1. Check API key: `OPENAI_API_KEY` in .env
2. Verify TTS_ENGINE is set to "openai"
3. Check internet connection
4. System will fallback to Edge TTS automatically

### Voice Quality Issues
1. Try different OpenAI voices (shimmer recommended for Arabic)
2. Ensure text is properly formatted
3. Check Egyptian dialect preprocessing results

### Performance
- OpenAI TTS: Higher quality, requires internet
- Edge TTS: Lower quality, works offline
- Fallback ensures minimal downtime

## Testing

Run the voice upgrade test:
```bash
python test_voice_upgrade.py
```

This will verify:
- Egyptian dialect preprocessing
- Provider availability
- Configuration loading
