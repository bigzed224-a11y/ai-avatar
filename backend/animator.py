"""Face animation module using SadTalker."""
import os
import uuid
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# SadTalker configuration
SADTALKER_DIR = Path(__file__).parent / "SadTalker"


def check_sadtalker_installed():
    """Check if SadTalker is installed."""
    return SADTALKER_DIR.exists() and (SADTALKER_DIR / "inference.py").exists()


def install_sadtalker():
    """Clone and setup SadTalker."""
    if check_sadtalker_installed():
        print("SadTalker already installed")
        return True
    
    print("Installing SadTalker...")
    try:
        # Clone the repo
        subprocess.run([
            "git", "clone", "--depth", "1",
            "https://github.com/OpenTalker/SadTalker.git",
            str(SADTALKER_DIR)
        ], check=True, capture_output=True)
        
        # Install requirements
        subprocess.run([
            "pip", "install", "-r", 
            str(SADTALKER_DIR / "requirements.txt")
        ], check=True, capture_output=True)
        
        # Download models
        subprocess.run([
            "python", str(SADTALKER_DIR / "scripts/download_models.sh")
        ], shell=True, check=True, capture_output=True)
        
        print("SadTalker installed successfully!")
        return True
    except Exception as e:
        print(f"Failed to install SadTalker: {e}")
        return False


def animate_face(photo_path: str, audio_path: str, result_id: str = None) -> str:
    """
    Generate lip-sync video from photo + audio using SadTalker.
    
    Args:
        photo_path: Path to character photo
        audio_path: Path to speech audio (WAV/MP3)
        result_id: Optional custom result ID
    
    Returns:
        Path to generated video
    """
    if not result_id:
        result_id = str(uuid.uuid4())
    
    output_path = OUTPUT_DIR / f"{result_id}.mp4"
    
    # Method 1: Use SadTalker via subprocess (if installed)
    if check_sadtalker_installed():
        return _run_sadtalker(photo_path, audio_path, output_path)
    
    # Method 2: Use SadTalker via Python API
    try:
        return _run_sadtalker_api(photo_path, audio_path, output_path)
    except ImportError:
        pass
    
    # Method 3: Use Wav2Lip as fallback
    try:
        return _run_wav2lip(photo_path, audio_path, output_path)
    except:
        pass
    
    # Method 4: Simple mouth movement animation (placeholder)
    return _generate_simple_animation(photo_path, audio_path, output_path)


def _run_sadtalker(photo_path: str, audio_path: str, output_path: Path) -> str:
    """Run SadTalker via command line."""
    result_id = output_path.stem
    
    cmd = [
        "python",
        str(SADTALKER_DIR / "inference.py"),
        "--driven_audio", audio_path,
        "--source_image", photo_path,
        "--result_dir", str(OUTPUT_DIR),
        "--checkpoint_dir", str(SADTALKER_DIR / "checkpoints"),
        "--enhancer", "gfpgan",  # Face enhancement
        "--still",  # Keep head still, only move mouth
        "--preprocess", "crop",  # Auto-crop face
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Find the generated video
    for f in OUTPUT_DIR.glob(f"{result_id}*.mp4"):
        return str(f)
    
    # If not found by ID, get the most recent
    videos = sorted(OUTPUT_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
    if videos:
        return str(videos[0])
    
    raise RuntimeError("SadTalker did not generate output")


def _run_sadtalker_api(photo_path: str, audio_path: str, output_path: Path) -> str:
    """Run SadTalker via Python API."""
    # Add SadTalker to path
    import sys
    sys.path.insert(0, str(SADTALKER_DIR))
    
    from sadtalker import SadTalker
    
    sadtalker = SadTalker(
        checkpoint_path=str(SADTALKER_DIR / "checkpoints"),
        config_path=str(SADTALKER_DIR / "src" / "config")
    )
    
    result = sadtalker.test(
        source_image=photo_path,
        driven_audio=audio_path,
        result_dir=str(output_path.parent),
        still_mode=True,
        preprocess="crop",
        enhancer="gfpgan"
    )
    
    return result.get("video_path", str(output_path))


def _run_wav2lip(photo_path: str, audio_path: str, output_path: Path) -> str:
    """Fallback to Wav2Lip for lip sync."""
    # This is a placeholder - actual Wav2Lip integration would go here
    raise NotImplementedError("Wav2Lip fallback not implemented")


def _generate_simple_animation(photo_path: str, audio_path: str, output_path: Path) -> str:
    """
    Generate simple mouth movement animation as placeholder.
    Uses OpenCV to create basic mouth movement overlay.
    """
    import cv2
    import numpy as np
    
    # Load the photo
    img = cv2.imread(photo_path)
    if img is None:
        raise ValueError(f"Could not load image: {photo_path}")
    
    height, width = img.shape[:2]
    
    # Get audio duration
    try:
        import wave
        with wave.open(audio_path, 'r') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)
    except:
        duration = 3.0  # Default 3 seconds
    
    # Create video
    fps = 25
    total_frames = int(duration * fps)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    # Create simple animation - slight scale pulsing to simulate talking
    for i in range(total_frames):
        frame = img.copy()
        
        # Simple mouth area highlight effect
        t = i / fps
        pulse = 1.0 + 0.02 * np.sin(2 * np.pi * 4 * t)  # 4Hz pulse
        
        # Apply subtle brightness change to lower face (mouth area)
        h, w = frame.shape[:2]
        mouth_region = frame[int(h*0.6):int(h*0.8), int(w*0.3):int(w*0.7)]
        if mouth_region.size > 0:
            mouth_region = (mouth_region * pulse).clip(0, 255).astype(np.uint8)
            frame[int(h*0.6):int(h*0.8), int(w*0.3):int(w*0.7)] = mouth_region
        
        out.write(frame)
    
    out.release()
    
    # Re-encode with proper codec
    final_output = str(output_path).replace('.mp4', '_final.mp4')
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(output_path),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        final_output
    ], capture_output=True)
    
    if os.path.exists(final_output):
        os.remove(str(output_path))
        os.rename(final_output, str(output_path))
    
    return str(output_path)


if __name__ == "__main__":
    # Test the animator
    print("Testing animator module...")
    print(f"SadTalker installed: {check_sadtalker_installed()}")
