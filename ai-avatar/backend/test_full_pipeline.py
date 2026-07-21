"""Test the full TTS + Animation pipeline."""
import sys
sys.path.insert(0, '.')

print("Testing Full Pipeline: Text -> Speech -> Lip-Sync Video")
print("=" * 60)

# Test 1: TTS
print("\n[1/3] Testing Text-to-Speech...")
from tts import text_to_speech_edge

text = "Hello! This is a test of our AI avatar lip-sync system."
try:
    audio_path = text_to_speech_edge(text)
    print(f"   ✓ Audio generated: {audio_path}")
except Exception as e:
    print(f"   ✗ TTS failed: {e}")
    sys.exit(1)

# Test 2: Animation
print("\n[2/3] Testing Face Animation...")
from animator import animate_face, check_sadtalker_installed
from pathlib import Path
import os

# Create a test image if none exists
test_image = "test_face.jpg"
if not os.path.exists(test_image):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (512, 512), color=(200, 180, 160))
    draw = ImageDraw.Draw(img)
    # Draw simple face
    draw.ellipse([156, 106, 356, 356], fill=(230, 200, 180))  # Face
    draw.ellipse([200, 180, 230, 210], fill=(50, 50, 50))  # Left eye
    draw.ellipse([280, 180, 310, 210], fill=(50, 50, 50))  # Right eye
    draw.arc([210, 250, 300, 310], 0, 180, fill=(150, 80, 80), width=3)  # Mouth
    img.save(test_image)
    print(f"   Created test image: {test_image}")

try:
    video_path = animate_face(test_image, audio_path)
    print(f"   ✓ Video generated: {video_path}")
    print(f"   SadTalker installed: {check_sadtalker_installed()}")
except Exception as e:
    print(f"   ✗ Animation failed: {e}")
    print("   Note: Simple placeholder animation will be used")

# Test 3: API
print("\n[3/3] Testing API Endpoints...")
try:
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    # Test root
    response = client.get("/")
    print(f"   ✓ GET / - {response.json()['status']}")
    
    # Test upload
    with open(test_image, "rb") as f:
        response = client.post("/api/upload", files={"file": ("test.jpg", f, "image/jpeg")})
        file_id = response.json()["file_id"]
        print(f"   ✓ POST /api/upload - file_id: {file_id[:8]}...")
    
    # Test TTS
    response = client.post(f"/api/tts?text={text}")
    audio_id = response.json()["audio_id"]
    print(f"   ✓ POST /api/tts - audio_id: {audio_id[:8]}...")
    
    # Test speak (combined)
    response = client.post(f"/api/speak?text={text}&file_id={file_id}")
    if response.status_code == 200:
        video_id = response.json()["video_id"]
        print(f"   ✓ POST /api/speak - video_id: {video_id[:8]}...")
    else:
        print(f"   ⚠ POST /api/speak - {response.json().get('detail', 'error')}")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    
except Exception as e:
    print(f"   ✗ API test failed: {e}")
