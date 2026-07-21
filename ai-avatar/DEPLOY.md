# Deployment Guide

This guide covers deploying your AI Avatar Lip-Sync app to various platforms.

## Quick Deploy Options

### Option 1: Railway (Recommended - Easiest)

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   ```bash
   # Initialize git and push to GitHub
   cd ai-avatar
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ai-avatar.git
   git push -u origin main
   ```

3. **Create New Project on Railway**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects the Dockerfile
   - Click "Deploy"

4. **Get Your URL**
   - Railway provides a public URL
   - Example: `https://ai-avatar-production.up.railway.app`

### Option 2: Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up

2. **Create New Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - Build Command: `pip install -r backend/requirements.txt`
     - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete

### Option 3: Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Initialize and Deploy**
   ```bash
   cd ai-avatar
   fly auth login
   fly launch
   fly deploy
   ```

### Option 4: Docker (Self-Hosted)

1. **Build Docker Image**
   ```bash
   cd ai-avatar
   docker build -t ai-avatar .
   ```

2. **Run Container**
   ```bash
   docker run -d -p 8000:8000 --name ai-avatar ai-avatar
   ```

3. **Access Your App**
   - Open `http://localhost:8000`

## Environment Variables

No environment variables are required for basic operation. The app works out of the box.

Optional:
- `PORT` - Server port (default: 8000)

## Post-Deployment Checklist

- [ ] Server is running (check health endpoint: `/`)
- [ ] Photo upload works
- [ ] TTS generation works
- [ ] Video generation works
- [ ] WebSocket connection works (real-time mode)

## Troubleshooting

### Build Fails
- Check that `ffmpeg` is installed in the Docker build
- Ensure all Python dependencies are in `requirements.txt`

### Server Starts but Features Don't Work
- Check server logs: `docker logs ai-avatar`
- Verify all directories exist: `uploads/`, `output/`

### WebSocket Not Connecting
- Ensure your hosting platform supports WebSockets
- Railway and Render support WebSockets by default

## Cost Estimates

| Platform | Free Tier | Paid Plans |
|----------|-----------|------------|
| Railway | $5 credit/month | From $5/month |
| Render | 750 hours/month | From $7/month |
| Fly.io | 3 shared VMs | From $5/month |
| Self-hosted | Depends on VPS | $5-20/month |

## Performance Notes

- First request may be slow (model loading)
- Video generation takes 5-60 seconds depending on:
  - Text length
  - Server hardware
  - GPU availability (optional)
- Consider adding a worker for production use

## Production Recommendations

1. **Add Rate Limiting** - Prevent abuse
2. **Add Authentication** - If needed
3. **Use Object Storage** - For generated videos (S3, R2)
4. **Add Caching** - Cache TTS audio for repeated text
5. **Monitor Usage** - Track API calls and storage

## Updating Your Deployment

```bash
# Push changes to GitHub
git add .
git commit -m "Update"
git push

# Railway/Render auto-deploy on push
# For Docker, rebuild and push:
docker build -t ai-avatar .
docker push YOUR_REGISTRY/ai-avatar
```

## Support

If you encounter issues:
1. Check the logs on your platform
2. Test locally first: `docker run -p 8000:8000 ai-avatar`
3. Open an issue on GitHub
