"""Higgsfield integration for high-quality video generation."""
import os
import json
import subprocess
import time
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Check if higgsfield CLI is available
def is_higgsfield_available():
    """Check if higgsfield CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["higgsfield", "auth", "token"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_higgsfield_token():
    """Get the current Higgsfield access token."""
    try:
        result = subprocess.run(
            ["higgsfield", "auth", "token"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def list_video_models():
    """List available video generation models."""
    try:
        result = subprocess.run(
            ["higgsfield", "model", "list", "--video", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def upload_image(image_path: str) -> str:
    """Upload an image to Higgsfield and return the upload ID."""
    try:
        result = subprocess.run(
            ["higgsfield", "upload", "media", image_path, "--json"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("id") or data.get("upload_id")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"[Higgsfield] Upload failed: {e}")
    return None


def generate_video_from_image(
    image_path: str,
    prompt: str = "Person speaking naturally with realistic lip sync and subtle head movements",
    model: str = "seedance_2_0",
    duration: int = 5,
    aspect_ratio: str = "16:9"
) -> dict:
    """
    Generate a video from an image using Higgsfield.
    
    Args:
        image_path: Path to the source image
        prompt: Description of the desired animation
        model: Model to use (seedance_2_0, kling_3_0, etc.)
        duration: Video duration in seconds
        aspect_ratio: Output aspect ratio
    
    Returns:
        Dict with job_id and status
    """
    if not is_higgsfield_available():
        return {"error": "Higgsfield not authenticated. Run: higgsfield auth login"}
    
    # Upload the image first
    upload_id = upload_image(image_path)
    if not upload_id:
        return {"error": "Failed to upload image"}
    
    # Create generation job
    try:
        cmd = [
            "higgsfield", "generate", "create", model,
            "--prompt", prompt,
            "--image", upload_id,
            "--duration", str(duration),
            "--aspect-ratio", aspect_ratio,
            "--json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "job_id": data.get("id"),
                "status": "queued",
                "message": "Video generation started"
            }
        else:
            return {"error": f"Generation failed: {result.stderr}"}
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"error": str(e)}


def wait_for_job(job_id: str, timeout: int = 300) -> dict:
    """Wait for a Higgsfield job to complete."""
    try:
        result = subprocess.run(
            ["higgsfield", "generate", "wait", job_id, "--json"],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return {"error": str(e)}
    return {"error": "Job wait failed"}


def download_video(job_id: str, output_path: str) -> str:
    """Download the generated video from a completed job."""
    try:
        # Get job details first
        result = subprocess.run(
            ["higgsfield", "generate", "get", job_id, "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video_url = data.get("output", {}).get("video_url")
            
            if video_url:
                # Download using curl
                dl_result = subprocess.run(
                    ["curl", "-L", "-o", output_path, video_url],
                    capture_output=True, text=True, timeout=120
                )
                if dl_result.returncode == 0:
                    return output_path
    except Exception as e:
        print(f"[Higgsfield] Download failed: {e}")
    return None


def generate_lip_sync_video(photo_path: str, audio_path: str) -> str:
    """
    Generate a lip-sync video using Higgsfield Seedance 2.0.
    Passes audio for lip-sync alignment.
    
    Args:
        photo_path: Path to the character photo
        audio_path: Path to the speech audio
    
    Returns:
        Path to the generated video
    """
    if not is_higgsfield_available():
        raise RuntimeError("Higgsfield not authenticated. Run: higgsfield auth login")
    
    result_id = str(int(time.time()))
    output_path = str(OUTPUT_DIR / f"higgsfield_{result_id}.mp4")
    
    # Upload audio for lip-sync
    audio_upload = upload_audio(audio_path)
    
    # Build command with audio flag for lip-sync
    cmd = [
        "higgsfield", "generate", "create", "seedance_2_0",
        "--prompt", "Person speaking naturally with realistic lip sync, subtle head movements, natural facial expressions",
        "--start-image", photo_path,
        "--audio", audio_path,
        "--duration", "8",
        "--aspect-ratio", "1:1",
        "--wait", "--json"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    if result.returncode != 0:
        raise RuntimeError(f"Higgsfield generation failed: {result.stderr}")
    
    data = json.loads(result.stdout)
    job_id = data.get("id")
    
    if not job_id:
        raise RuntimeError("No job ID returned from Higgsfield")
    
    # Download result
    downloaded = download_video(job_id, output_path)
    if downloaded:
        return downloaded
    
    raise RuntimeError("Failed to download generated video")


def upload_audio(audio_path: str) -> str:
    """Upload an audio file to Higgsfield."""
    try:
        result = subprocess.run(
            ["higgsfield", "upload", "media", audio_path, "--json"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("id") or data.get("upload_id")
    except Exception as e:
        print(f"[Higgsfield] Audio upload failed: {e}")
    return None


if __name__ == "__main__":
    print("Higgsfield Integration Module")
    print(f"Available: {is_higgsfield_available()}")
    
    if is_higgsfield_available():
        print("\nAvailable video models:")
        models = list_video_models()
        if models:
            print(json.dumps(models, indent=2))
        else:
            print("Could not fetch models")
    else:
        print("\nTo authenticate, run: higgsfield auth login")
