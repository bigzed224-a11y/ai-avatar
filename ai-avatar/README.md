# AI Avatar Lip-Sync Web App

Upload a photo, choose a voice, type text, and watch your avatar speak with realistic lip-sync animation!

![Version](https://img.shields.io/badge/Version-2.0-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)

## Features

- **Photo Upload** - Drag & drop your character image
- **8 Voice Options** - Male/female, US/UK accents
- **Text-to-Speech** - Natural voice generation
- **Lip-Sync Video** - Photo speaks your text
- **Real-Time Mode** - Avatar mirrors your head via webcam
- **Video History** - Access all generated videos
- **Download** - Save as MP4

## Quick Start

### Local Development

```bash
# Clone and setup
cd ai-avatar
python -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
sudo apt-get install ffmpeg

# Start server
python main.py
```

Open `frontend/index.html` in your browser.

### Docker

```bash
docker build -t ai-avatar .
docker run -p 8000:8000 ai-avatar
```

## Deployment

### Railway (Recommended)

1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repo
5. Done! Your app is live.

See [DEPLOY.md](DEPLOY.md) for detailed instructions.

### Other Platforms

- **Render** - See `render.yaml`
- **Fly.io** - Run `fly launch && fly deploy`
- **Heroku** - Uses `Procfile`

## Project Structure

```
ai-avatar/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── tts.py            # Text-to-Speech (8 voices)
│   ├── animator.py       # Face animation
│   ├── pose.py           # Pose detection
│   └── requirements.txt
├── frontend/
│   ├── index.html        # Main UI
│   ├── realtime.html     # Real-time pose UI
│   ├── style.css
│   ├── app.js
│   └── realtime.js
├── Dockerfile            # Docker build
├── railway.json          # Railway config
├── render.yaml           # Render config
├── Procfile              # Heroku config
└── DEPLOY.md             # Deployment guide
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Server status |
| `GET /api/voices` | List voices |
| `POST /api/upload` | Upload photo |
| `POST /api/tts` | Generate speech |
| `POST /api/speak` | **Generate video** |
| `GET /api/video/{id}` | Download video |
| `GET /api/history` | Video history |
| `WS /ws/pose` | Real-time pose |

## Usage

### Text-to-Lip-Sync
1. Upload character photo
2. Select voice (Aria, Guy, etc.)
3. Type text
4. Click "Generate"
5. Download your video!

### Real-Time Mode
1. Click "Real-Time Mode →"
2. Upload avatar photo
3. Start camera
4. Move your head - avatar follows!

## Development Phases

- [x] Phase 1: Project setup
- [x] Phase 2: Text-to-speech
- [x] Phase 3: Face animation
- [x] Phase 4: Polish & UX
- [x] Phase 5: Real-time pose
- [x] Phase 6: Voice options & history

## Credits

- [edge-tts](https://github.com/rany2/edge-tts) - Microsoft voices
- [MediaPipe](https://google.github.io/mediapipe/) - Pose detection
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
