"""Text-to-Speech module with multiple voice options."""
import os
import uuid
import asyncio
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

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


async def text_to_speech_edge(text: str, voice: str = None) -> str:
    """
    Convert text to speech using edge-tts with fallback to gTTS.
    
    Args:
        text: Text to convert
        voice: Voice ID (e.g., 'aria', 'guy') or full voice name
    
    Returns:
        Path to generated audio file
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Resolve voice name
    if voice and voice in VOICE_OPTIONS:
        voice_name = VOICE_OPTIONS[voice]["voice"]
    elif voice and "." in voice:
        voice_name = voice
    else:
        voice_name = VOICE_OPTIONS[DEFAULT_VOICE]["voice"]
    
    audio_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{audio_id}.mp3"
    
    edge_error = None
    gtts_error = None
    
    # Try edge-tts first
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(str(output_path))
        print(f"[TTS] edge-tts succeeded for voice: {voice_name}")
        return str(output_path)
    except Exception as e:
        edge_error = str(e)
        print(f"[TTS] edge-tts failed: {edge_error}, falling back to gTTS")
    
    # Fallback to gTTS (Google Text-to-Speech)
    try:
        from gtts import gTTS
        
        # Map voice to language accent
        lang = 'en'
        tld = 'com'
        if voice_name.startswith('en-GB'):
            tld = 'co.uk'
        elif voice_name.startswith('en-AU'):
            tld = 'com.au'
        
        tts = gTTS(text=text, lang=lang, tld=tld)
        tts.save(str(output_path))
        print(f"[TTS] gTTS fallback succeeded")
        return str(output_path)
    except Exception as e:
        gtts_error = str(e)
        print(f"[TTS] gTTS also failed: {gtts_error}")
    
    raise RuntimeError(f"All TTS engines failed. edge-tts: {edge_error}, gTTS: {gtts_error}")


def get_available_voices():
    """Get list of available voices."""
    return VOICE_OPTIONS


if __name__ == "__main__":
    print("Testing available voices:")
    for key, info in VOICE_OPTIONS.items():
        print(f"  {key}: {info['name']}")
    
    print("\nGenerating test audio...")
    audio_path = asyncio.run(text_to_speech_edge("Hello! This is a test."))
    print(f"Audio saved to: {audio_path}")
