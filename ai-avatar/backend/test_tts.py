"""Quick test for TTS functionality."""
import sys
sys.path.insert(0, '.')

from tts import text_to_speech_edge

print("Testing edge-tts (lightweight option)...")
text = "Hello! This is a test of the text to speech system for our AI avatar."

try:
    audio_path = text_to_speech_edge(text)
    print(f"Success! Audio saved to: {audio_path}")
except Exception as e:
    print(f"Error: {e}")
