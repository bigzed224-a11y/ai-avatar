"""Text-to-Speech module with multiple voice options."""
import os
import uuid
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Lazy-load TTS model
_tts_model = None

# Available voices for edge-tts
VOICE_OPTIONS = {
    "aria": {
        "name": "Aria (Female, US)",
        "voice": "en-US-AriaNeural",
        "gender": "female"
    },
    "guy": {
        "name": "Guy (Male, US)",
        "voice": "en-US-GuyNeural",
        "gender": "male"
    },
    "davis": {
        "name": "Davis (Male, US)",
        "voice": "en-US-DavisNeural",
        "gender": "male"
    },
    "jenny": {
        "name": "Jenny (Female, US)",
        "voice": "en-US-JennyNeural",
        "gender": "female"
    },
    "tony": {
        "name": "Tony (Male, US)",
        "voice": "en-US-TonyNeural",
        "gender": "male"
    },
    "nancy": {
        "name": "Nancy (Female, US)",
        "voice": "en-US-NancyNeural",
        "gender": "female"
    },
    "andy": {
        "name": "Andy (Male, UK)",
        "voice": "en-GB-AndyNeural",
        "gender": "male"
    },
    "sonia": {
        "name": "Sonia (Female, UK)",
        "voice": "en-GB-SoniaNeural",
        "gender": "female"
    }
}

DEFAULT_VOICE = "aria"


def get_tts_model():
    """Load Coqui TTS model on first use."""
    global _tts_model
    if _tts_model is None:
        print("Loading TTS model...")
        from TTS.api import TTS
        _tts_model = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
        print("TTS model loaded!")
    return _tts_model


def text_to_speech(text: str, speaker: str = None) -> str:
    """Convert text to speech using Coqui TTS."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    audio_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{audio_id}.wav"
    
    tts = get_tts_model()
    tts.tts_to_file(text=text, file_path=str(output_path))
    
    return str(output_path)


def text_to_speech_edge(text: str, voice: str = None) -> str:
    """
    Convert text to speech using edge-tts.
    
    Args:
        text: Text to convert
        voice: Voice ID (e.g., 'aria', 'guy') or full voice name
    
    Returns:
        Path to generated audio file
    """
    import asyncio
    import edge_tts
    
    # Resolve voice name
    if voice and voice in VOICE_OPTIONS:
        voice_name = VOICE_OPTIONS[voice]["voice"]
    elif voice and "." in voice:
        voice_name = voice  # Already full name like "en-US-AriaNeural"
    else:
        voice_name = VOICE_OPTIONS[DEFAULT_VOICE]["voice"]
    
    audio_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{audio_id}.mp3"
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(str(output_path))
    
    asyncio.run(generate())
    return str(output_path)


def get_available_voices():
    """Get list of available voices."""
    return VOICE_OPTIONS


def text_to_speech_with_effects(text: str, voice: str = None, 
                                 rate: str = "+0%", pitch: str = "+0Hz") -> str:
    """
    Generate speech with rate and pitch adjustments.
    
    Args:
        text: Text to speak
        voice: Voice ID
        rate: Speed adjustment (e.g., "+20%", "-10%")
        pitch: Pitch adjustment (e.g., "+5Hz", "-2Hz")
    
    Returns:
        Path to audio file
    """
    import asyncio
    import edge_tts
    
    # Resolve voice
    if voice and voice in VOICE_OPTIONS:
        voice_name = VOICE_OPTIONS[voice]["voice"]
    else:
        voice_name = VOICE_OPTIONS[DEFAULT_VOICE]["voice"]
    
    audio_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{audio_id}.mp3"
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice_name, rate=rate, pitch=pitch)
        await communicate.save(str(output_path))
    
    asyncio.run(generate())
    return str(output_path)


if __name__ == "__main__":
    # Test voices
    print("Testing available voices:")
    for key, info in VOICE_OPTIONS.items():
        print(f"  {key}: {info['name']}")
    
    print("\nGenerating test audio with default voice...")
    audio_path = text_to_speech_edge("Hello! This is a test of different voices.")
    print(f"Audio saved to: {audio_path}")
