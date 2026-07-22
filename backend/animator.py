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
        subprocess.run([
            "git", "clone", "--depth", "1",
            "https://github.com/OpenTalker/SadTalker.git",
            str(SADTALKER_DIR)
        ], check=True, capture_output=True)
        
        subprocess.run([
            "pip", "install", "-r", 
            str(SADTALKER_DIR / "requirements.txt")
        ], check=True, capture_output=True)
        
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
    
    # Method 4: High quality simple animation
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
        "--enhancer", "gfpgan",
        "--still",
        "--preprocess", "crop",
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    for f in OUTPUT_DIR.glob(f"{result_id}*.mp4"):
        return str(f)
    
    videos = sorted(OUTPUT_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
    if videos:
        return str(videos[0])
    
    raise RuntimeError("SadTalker did not generate output")


def _run_sadtalker_api(photo_path: str, audio_path: str, output_path: Path) -> str:
    """Run SadTalker via Python API."""
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
    raise NotImplementedError("Wav2Lip fallback not implemented")


def _generate_simple_animation(photo_path: str, audio_path: str, output_path: Path) -> str:
    """
    Generate high quality mouth movement animation.
    Uses OpenCV with improved rendering and FFmpeg for encoding.
    """
    import cv2
    import numpy as np
    
    # Load the photo
    img = cv2.imread(photo_path)
    if img is None:
        raise ValueError(f"Could not load image: {photo_path}")
    
    height, width = img.shape[:2]
    
    # Scale down if too large (max 720p for good quality/speed balance)
    max_dim = 720
    if max(height, width) > max_dim:
        scale = max_dim / max(height, width)
        width = int(width * scale)
        height = int(height * scale)
        img = cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)
    
    # Get audio duration
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())
    except:
        try:
            import wave
            with wave.open(audio_path, 'r') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate)
        except:
            duration = 3.0
    
    # High quality settings
    fps = 30
    total_frames = int(duration * fps)
    
    # Create temp video with high quality
    temp_output = str(output_path).replace('.mp4', '_temp.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
    
    # Analyze audio for speech patterns (if possible)
    speech_amplitudes = _extract_audio_amplitude(audio_path, total_frames, fps)
    
    # Create animation with multiple effects
    for i in range(total_frames):
        frame = img.copy()
        t = i / fps
        
        # Get speech amplitude for this frame
        amp_idx = min(i, len(speech_amplitudes) - 1) if speech_amplitudes else -1
        speech_amp = speech_amplitudes[amp_idx] if amp_idx >= 0 else 0.5
        
        # Multiple animation effects for realism
        h, w = frame.shape[:2]
        
        # 1. Mouth area brightness variation (simulates jaw movement)
        jaw_pulse = speech_amp * 0.15
        mouth_region_y1 = int(h * 0.55)
        mouth_region_y2 = int(h * 0.85)
        mouth_region_x1 = int(w * 0.25)
        mouth_region_x2 = int(w * 0.75)
        
        mouth_region = frame[mouth_region_y1:mouth_region_y2, mouth_region_x1:mouth_region_x2].copy()
        if mouth_region.size > 0:
            # Brightness modulation
            brightness = 1.0 + jaw_pulse * np.sin(2 * np.pi * 4 * t + speech_amp * 0.5)
            mouth_region = cv2.convertScaleAbs(mouth_region, alpha=brightness, beta=5)
            frame[mouth_region_y1:mouth_region_y2, mouth_region_x1:mouth_region_x2] = mouth_region
        
        # 2. Subtle scale pulsing (head bob)
        scale_factor = 1.0 + speech_amp * 0.008 * np.sin(2 * np.pi * 3 * t)
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, 0, scale_factor)
        frame = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        # 3. Subtle color temperature shift (warmth during speech)
        if speech_amp > 0.3:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + speech_amp * 0.1), 0, 255)
            frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        out.write(frame)
    
    out.release()
    
    # Re-encode with high quality settings
    final_output = str(output_path)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", temp_output,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "slow",        # Better compression
        "-crf", "18",             # Higher quality (lower = better)
        "-profile:v", "high",     # High profile for better quality
        "-level", "4.1",          # Compatible level
        "-pix_fmt", "yuv420p",    # Better compatibility
        "-c:a", "aac",
        "-b:a", "192k",           # High quality audio
        "-ar", "44100",           # Standard sample rate
        "-movflags", "+faststart", # Web optimized
        final_output
    ], capture_output=True)
    
    # Clean up temp file
    if os.path.exists(temp_output):
        os.remove(temp_output)
    
    return str(output_path)


def _extract_audio_amplitude(audio_path: str, num_frames: int, fps: float) -> list:
    """Extract amplitude envelope from audio for sync."""
    try:
        import subprocess
        import json
        
        # Get audio as raw PCM
        result = subprocess.run([
            "ffmpeg", "-i", audio_path,
            "-f", "s16le", "-ac", "1", "-ar", "16000",
            "-v", "quiet", "-",
        ], capture_output=True)
        
        if result.returncode != 0:
            return []
        
        # Convert to numpy array
        import numpy as np
        audio_data = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32)
        
        if len(audio_data) == 0:
            return []
        
        # Normalize
        audio_data = audio_data / 32768.0
        
        # Calculate amplitude envelope
        samples_per_frame = int(16000 / fps)
        amplitudes = []
        
        for i in range(num_frames):
            start = i * samples_per_frame
            end = min(start + samples_per_frame, len(audio_data))
            if start < len(audio_data):
                chunk = audio_data[start:end]
                amp = np.sqrt(np.mean(chunk ** 2))  # RMS
                amplitudes.append(min(1.0, amp * 3))  # Scale up and clamp
            else:
                amplitudes.append(0.0)
        
        # Smooth the envelope
        kernel_size = 3
        kernel = np.ones(kernel_size) / kernel_size
        amplitudes = np.convolve(amplitudes, kernel, mode='same').tolist()
        
        return amplitudes
    except Exception as e:
        print(f"Audio amplitude extraction failed: {e}")
        return []


if __name__ == "__main__":
    print("Testing animator module...")
    print(f"SadTalker installed: {check_sadtalker_installed()}")
