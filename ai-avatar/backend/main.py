from fastapi import FastAPI, UploadFile, File, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import uuid
import os
import time
import json

app = FastAPI(title="AI Avatar Lip-Sync API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory stores
uploaded_photos = {}
generated_audio = {}
generated_videos = {}
processing_jobs = {}
video_history = []  # Track all generated videos

# WebSocket connections
active_connections = []


@app.get("/")
async def root():
    from animator import check_sadtalker_installed
    return {
        "message": "AI Avatar Lip-Sync API",
        "status": "running",
        "version": "2.0.0",
        "features": ["tts", "animation", "realtime-pose", "voice-options", "history"]
    }


# ===== VOICE ENDPOINTS =====

@app.get("/api/voices")
async def get_voices():
    """Get available voice options."""
    from tts import get_available_voices
    return {
        "voices": get_available_voices(),
        "default": "aria"
    }


# ===== UPLOAD ENDPOINTS =====

@app.post("/api/upload")
async def upload_photo(file: UploadFile = File(...)):
    """Upload a character photo for lip-sync animation."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix or ".jpg"
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    uploaded_photos[file_id] = {
        "path": str(file_path),
        "filename": file.filename,
        "uploaded_at": time.time()
    }

    return {
        "file_id": file_id,
        "filename": file.filename,
        "message": "Photo uploaded successfully",
        "preview_url": f"/api/photo/{file_id}"
    }


@app.get("/api/photo/{file_id}")
async def get_photo(file_id: str):
    """Get uploaded photo by ID."""
    if file_id not in uploaded_photos:
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(uploaded_photos[file_id]["path"])


@app.get("/api/photos")
async def list_photos():
    """List all uploaded photos."""
    return {
        "photos": [
            {"file_id": fid, "filename": info["filename"], "preview_url": f"/api/photo/{fid}"}
            for fid, info in uploaded_photos.items()
        ],
        "count": len(uploaded_photos)
    }


# ===== TTS ENDPOINTS =====

@app.post("/api/tts")
async def text_to_speech(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query(None, description="Voice ID (e.g., 'aria', 'guy')")
):
    """Generate speech from text using TTS."""
    from tts import text_to_speech_edge
    
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
    
    try:
        audio_path = text_to_speech_edge(text, voice=voice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
    
    audio_id = Path(audio_path).stem
    generated_audio[audio_id] = {
        "path": audio_path,
        "text": text,
        "voice": voice,
        "created_at": time.time()
    }
    
    return {
        "audio_id": audio_id,
        "audio_url": f"/api/audio/{audio_id}",
        "message": "Speech generated successfully",
        "text": text,
        "voice": voice
    }


@app.get("/api/audio/{audio_id}")
async def get_audio(audio_id: str):
    """Get generated audio file by ID."""
    if audio_id not in generated_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    audio_path = generated_audio[audio_id]["path"]
    media_type = "audio/wav" if audio_path.endswith(".wav") else "audio/mpeg"
    return FileResponse(audio_path, media_type=media_type)


# ===== ANIMATION ENDPOINTS =====

@app.post("/api/animate")
async def animate_photo(file_id: str = Query(...), audio_id: str = Query(...)):
    """Generate lip-sync video from photo + audio."""
    from animator import animate_face
    
    if file_id not in uploaded_photos:
        raise HTTPException(status_code=404, detail="Photo not found")
    if audio_id not in generated_audio:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    photo_path = uploaded_photos[file_id]["path"]
    audio_path = generated_audio[audio_id]["path"]
    
    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "processing", "started_at": time.time()}
    
    try:
        video_path = animate_face(photo_path, audio_path)
    except Exception as e:
        processing_jobs[job_id]["status"] = "failed"
        raise HTTPException(status_code=500, detail=f"Animation failed: {str(e)}")
    
    video_id = Path(video_path).stem
    generated_videos[video_id] = {
        "path": video_path,
        "file_id": file_id,
        "audio_id": audio_id,
        "created_at": time.time()
    }
    
    # Add to history
    video_history.append({
        "video_id": video_id,
        "file_id": file_id,
        "filename": uploaded_photos[file_id]["filename"],
        "text": generated_audio[audio_id].get("text", ""),
        "created_at": time.time()
    })
    
    processing_jobs[job_id]["status"] = "completed"
    
    return {
        "video_id": video_id,
        "video_url": f"/api/video/{video_id}",
        "message": "Animation generated successfully"
    }


@app.get("/api/video/{video_id}")
async def get_video(video_id: str):
    """Get generated video file by ID."""
    if video_id not in generated_videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        generated_videos[video_id]["path"],
        media_type="video/mp4",
        filename=f"avatar_{video_id[:8]}.mp4"
    )


@app.post("/api/speak")
async def speak(
    text: str = Query(...),
    file_id: str = Query(...),
    voice: str = Query(None)
):
    """Combined TTS + animation in one call."""
    from tts import text_to_speech_edge
    from animator import animate_face
    
    if file_id not in uploaded_photos:
        raise HTTPException(status_code=404, detail="Photo not found")
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {"status": "tts", "started_at": time.time()}
    
    # Generate TTS
    try:
        audio_path = text_to_speech_edge(text, voice=voice)
    except Exception as e:
        processing_jobs[job_id]["status"] = "failed"
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
    
    processing_jobs[job_id]["status"] = "animating"
    
    # Generate animation
    photo_path = uploaded_photos[file_id]["path"]
    try:
        video_path = animate_face(photo_path, audio_path)
    except Exception as e:
        processing_jobs[job_id]["status"] = "failed"
        raise HTTPException(status_code=500, detail=f"Animation failed: {str(e)}")
    
    video_id = Path(video_path).stem
    generated_videos[video_id] = {
        "path": video_path,
        "file_id": file_id,
        "audio_path": audio_path,
        "text": text,
        "voice": voice,
        "created_at": time.time()
    }
    
    # Add to history
    video_history.append({
        "video_id": video_id,
        "file_id": file_id,
        "filename": uploaded_photos[file_id]["filename"],
        "text": text,
        "voice": voice,
        "created_at": time.time()
    })
    
    processing_jobs[job_id]["status"] = "completed"
    
    return {
        "video_id": video_id,
        "video_url": f"/api/video/{video_id}",
        "message": "Lip-sync video generated successfully",
        "text": text,
        "voice": voice
    }


# ===== HISTORY ENDPOINTS =====

@app.get("/api/history")
async def get_history(limit: int = Query(20, ge=1, le=100)):
    """Get video generation history."""
    return {
        "history": video_history[-limit:][::-1],  # Newest first
        "total": len(video_history)
    }


@app.delete("/api/history/{video_id}")
async def delete_from_history(video_id: str):
    """Delete a video from history."""
    global video_history
    
    if video_id not in generated_videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete file
    video_path = generated_videos[video_id]["path"]
    if os.path.exists(video_path):
        os.remove(video_path)
    
    # Remove from stores
    del generated_videos[video_id]
    video_history = [v for v in video_history if v["video_id"] != video_id]
    
    return {"message": "Video deleted", "video_id": video_id}


@app.delete("/api/cleanup")
async def cleanup_old_files():
    """Clean up old files (older than 1 hour)."""
    cutoff = time.time() - 3600
    cleaned = {"uploads": 0, "output": 0}
    
    for path in UPLOAD_DIR.glob("*"):
        if path.stat().st_mtime < cutoff:
            path.unlink()
            cleaned["uploads"] += 1
    
    for path in OUTPUT_DIR.glob("*"):
        if path.stat().st_mtime < cutoff:
            path.unlink()
            cleaned["output"] += 1
    
    return {"message": "Cleanup completed", "cleaned": cleaned}


# ===== JOB STATUS =====

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Check processing job status."""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "elapsed": time.time() - job["started_at"]
    }


# ===== WEBSOCKET =====

@app.websocket("/ws/pose")
async def websocket_pose(websocket: WebSocket):
    """WebSocket endpoint for real-time pose data."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            pose_data = json.loads(data)
            
            from pose import process_pose_frame
            animation_params = process_pose_frame(pose_data.get("landmarks", []))
            
            await websocket.send_json({
                "type": "animation",
                "params": animation_params
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
