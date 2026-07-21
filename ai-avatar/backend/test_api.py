"""Test API endpoints."""
import requests
import sys

API_BASE = "http://localhost:8000"

def test_api():
    print("Testing AI Avatar Lip-Sync API")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n[1] Testing root endpoint...")
    try:
        r = requests.get(f"{API_BASE}/")
        print(f"   ✓ Status: {r.json()['status']}")
        print(f"   ✓ SadTalker: {r.json()['sadtalker']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 2: Upload photo
    print("\n[2] Testing photo upload...")
    try:
        # Create a test image
        from PIL import Image
        img = Image.new('RGB', (256, 256), color=(100, 150, 200))
        img.save("/tmp/test_avatar.jpg")
        
        with open("/tmp/test_avatar.jpg", "rb") as f:
            r = requests.post(f"{API_BASE}/api/upload", files={"file": ("test.jpg", f, "image/jpeg")})
        file_id = r.json()["file_id"]
        print(f"   ✓ Uploaded: {file_id[:8]}...")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 3: TTS
    print("\n[3] Testing TTS...")
    try:
        r = requests.post(f"{API_BASE}/api/tts?text=Hello, this is a test")
        audio_id = r.json()["audio_id"]
        print(f"   ✓ Generated: {audio_id[:8]}...")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 4: Combined speak
    print("\n[4] Testing combined TTS + Animation...")
    try:
        r = requests.post(f"{API_BASE}/api/speak?text=Testing the avatar&file_id={file_id}")
        if r.status_code == 200:
            video_id = r.json()["video_id"]
            print(f"   ✓ Video: {video_id[:8]}...")
        else:
            print(f"   ⚠ {r.json().get('detail', 'Error')}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("API tests completed!")
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
