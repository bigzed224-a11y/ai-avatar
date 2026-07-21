"""Test voice options."""
import requests

API_BASE = "http://localhost:8000"

def test_voices():
    print("Testing Voice Options")
    print("=" * 50)
    
    # Get available voices
    r = requests.get(f"{API_BASE}/api/voices")
    voices = r.json()["voices"]
    
    print(f"\nAvailable voices ({len(voices)}):")
    for key, info in voices.items():
        print(f"  {key}: {info['name']} ({info['gender']})")
    
    # Test each voice
    print("\nTesting voice generation:")
    for voice_key in ["aria", "guy"]:
        try:
            r = requests.post(f"{API_BASE}/api/tts?text=Hello, I am {voice_key}&voice={voice_key}")
            if r.status_code == 200:
                print(f"  ✓ {voice_key}: Generated successfully")
            else:
                print(f"  ✗ {voice_key}: {r.json().get('detail', 'Error')}")
        except Exception as e:
            print(f"  ✗ {voice_key}: {e}")

if __name__ == "__main__":
    test_voices()
