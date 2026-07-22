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
    Convert text to speech using edge-tts (async version for FastAPI).
    
    Args:
        text: Text to convert
        voice: Voice ID (e.g., 'aria', 'guy') or full voice name
    
    Returns:
        Path to generated audio file
    """
    import edge_tts
    
    # Resolve voice name
    if voice and voice in VOICE_OPTIONS:
        voice_name = VOICE_OPTIONS[voice]["voice"]
    elif voice and "." in voice:
        voice_name = voice
    else:
        voice_name = VOICE_OPTIONS[DEFAULT_VOICE]["voice"]
    
    audio_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{audio_id}.mp3"
    
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(str(output_path))
    
    return str(output_path)


def text_to_speech_sync(text: str, voice: str = None) -> str:
    """
    Synchronous version for non-async contexts.
    """
    import edge_tts
    
    if voice and voice in VOICE_OPTIONS:
        voice_name = VOICE_OPTIONS[voice]["voice"]
    elif voice and "." in voice:
        voice_name = voice
    else:
        voice_name = VOICE_OPTIONS[DEFAULT_VOICE]["voice"]
    
    audio_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{audio_id}.mp3"
    
    async def generate():
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(str(output_path))
    
    # Check if there's already a running event loop
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - use nest_asyncio or create a task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(asyncio.run, generate()).result()
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        asyncio.run(generate())
    
    return str(output_path)


def get_available_voices():
    """Get list of available voices."""
    return VOICE_OPTIONS


if __name__ == "__main__":
    print("Testing available voices:")
    for key, info in VOICE_OPTIONS.items():
        print(f"  {key}: {info['name']}")
    
    print("\nGenerating test audio...")
    audio_path = text_to_speech_sync("Hello! This is a test.")
    print(f"Audio saved to: {audio_path}")
