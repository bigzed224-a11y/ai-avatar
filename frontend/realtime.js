// Real-Time Pose Detection Module

class RealtimePoseController {
    constructor() {
        this.videoElement = document.getElementById('webcam-video');
        this.avatarCanvas = document.getElementById('avatar-canvas');
        this.poseCanvas = document.getElementById('pose-canvas');
        this.poseOverlay = document.getElementById('pose-overlay');
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.wsStatus = document.getElementById('ws-status');
        this.wsStatusText = document.getElementById('ws-status-text');
        
        this.avatarCtx = this.avatarCanvas.getContext('2d');
        this.poseCtx = this.poseCanvas.getContext('2d');
        
        this.avatarImage = null;
        this.ws = null;
        this.camera = null;
        this.pose = null;
        this.isRunning = false;
        
        this.currentPose = {
            headTilt: 0,
            headNod: 0,
            headTurn: 0
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupFileUpload();
    }
    
    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.start());
        this.stopBtn.addEventListener('click', () => this.stop());
    }
    
    setupFileUpload() {
        const dropZone = document.getElementById('drop-zone');
        const photoInput = document.getElementById('photo-input');
        const previewContainer = document.getElementById('preview-container');
        const photoPreview = document.getElementById('photo-preview');
        const photoName = document.getElementById('photo-name');
        
        dropZone.addEventListener('click', () => photoInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                this.loadAvatarImage(file);
            }
        });
        
        photoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) this.loadAvatarImage(file);
        });
    }
    
    loadAvatarImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                this.avatarImage = img;
                
                // Update UI
                document.getElementById('photo-preview').src = e.target.result;
                document.getElementById('photo-name').textContent = file.name;
                document.getElementById('preview-container').classList.remove('hidden');
                document.getElementById('drop-zone').classList.add('hidden');
                document.getElementById('realtime-section').classList.add('active');
                
                // Draw initial avatar
                this.drawAvatar(0, 0, 0);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    async start() {
        if (this.isRunning) return;
        
        try {
            // Setup WebSocket
            this.connectWebSocket();
            
            // Setup MediaPipe Pose
            await this.setupPose();
            
            // Setup camera
            await this.setupCamera();
            
            this.isRunning = true;
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            
        } catch (error) {
            console.error('Failed to start:', error);
            alert('Failed to start camera: ' + error.message);
        }
    }
    
    stop() {
        this.isRunning = false;
        
        if (this.camera) {
            this.camera.stop();
        }
        
        if (this.ws) {
            this.ws.close();
        }
        
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.updateConnectionStatus(false);
    }
    
    connectWebSocket() {
        const wsUrl = `ws://${window.location.hostname}:8000/ws/pose`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'animation') {
                this.updatePoseFromServer(data.params);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }
    
    updateConnectionStatus(connected) {
        this.wsStatus.classList.toggle('connected', connected);
        this.wsStatusText.textContent = connected ? 'Connected' : 'Disconnected';
    }
    
    async setupPose() {
        return new Promise((resolve, reject) => {
            this.pose = new Pose({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/pose@0.4.1646424915/${file}`;
                }
            });
            
            this.pose.setOptions({
                modelComplexity: 1,
                smoothLandmarks: true,
                enableSegmentation: false,
                smoothSegmentation: false,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });
            
            this.pose.onResults((results) => this.onPoseResults(results));
            
            this.pose.initialize().then(resolve).catch(reject);
        });
    }
    
    async setupCamera() {
        return new Promise((resolve, reject) => {
            this.camera = new Camera(this.videoElement, {
                onFrame: async () => {
                    if (this.isRunning && this.pose) {
                        await this.pose.send({ image: this.videoElement });
                    }
                },
                width: 640,
                height: 480
            });
            
            this.camera.start().then(resolve).catch(reject);
        });
    }
    
    onPoseResults(results) {
        if (!results.poseLandmarks) {
            this.poseOverlay.textContent = 'Pose: No person detected';
            return;
        }
        
        // Extract key landmarks
        const landmarks = results.poseLandmarks;
        
        // Calculate pose values
        const nose = landmarks[0];
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        
        // Head tilt (left/right)
        const shoulderDiff = leftShoulder.y - rightShoulder.y;
        const tilt = Math.max(-1, Math.min(1, shoulderDiff * 5));
        
        // Head turn (left/right)
        const shoulderCenterX = (leftShoulder.x + rightShoulder.x) / 2;
        const turn = Math.max(-1, Math.min(1, (nose.x - shoulderCenterX) * 3));
        
        // Head nod (up/down)
        const nod = Math.max(-1, Math.min(1, (nose.y - 0.5) * 2));
        
        // Update current pose with smoothing
        this.currentPose.headTilt = this.smooth(this.currentPose.headTilt, tilt);
        this.currentPose.headNod = this.smooth(this.currentPose.headNod, nod);
        this.currentPose.headTurn = this.smooth(this.currentPose.headTurn, turn);
        
        // Update UI values
        document.getElementById('val-tilt').textContent = this.currentPose.headTilt.toFixed(2);
        document.getElementById('val-nod').textContent = this.currentPose.headNod.toFixed(2);
        document.getElementById('val-turn').textContent = this.currentPose.headTurn.toFixed(2);
        
        // Update overlay
        this.poseOverlay.textContent = `Pose: Tracking`;
        
        // Send to server via WebSocket
        this.sendPoseData(landmarks);
        
        // Draw avatar with current pose
        this.drawAvatar(
            this.currentPose.headTilt,
            this.currentPose.headNod,
            this.currentPose.headTurn
        );
    }
    
    smooth(current, target, factor = 0.3) {
        return current + (target - current) * factor;
    }
    
    sendPoseData(landmarks) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                landmarks: landmarks.map(l => ({
                    x: l.x,
                    y: l.y,
                    z: l.z,
                    visibility: l.visibility
                }))
            }));
        }
    }
    
    updatePoseFromServer(params) {
        // Server can override or enhance local pose calculations
        if (params.head_rotation) {
            // Use server-processed values if available
        }
    }
    
    drawAvatar(tilt, nod, turn) {
        if (!this.avatarImage) return;
        
        const canvas = this.avatarCanvas;
        const ctx = this.avatarCtx;
        
        // Set canvas size to match image
        canvas.width = this.avatarImage.width;
        canvas.height = this.avatarImage.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Save context
        ctx.save();
        
        // Apply transformations based on pose
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        
        ctx.translate(centerX, centerY);
        
        // Apply rotation based on tilt and turn
        const rotationZ = tilt * 0.15; // Tilt
        const rotationY = turn * 0.2;  // Turn
        const translationY = nod * 20;  // Nod
        
        ctx.rotate(rotationZ);
        ctx.translate(0, translationY);
        
        // Draw the avatar image
        ctx.drawImage(
            this.avatarImage,
            -canvas.width / 2,
            -canvas.height / 2,
            canvas.width,
            canvas.height
        );
        
        // Restore context
        ctx.restore();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the realtime page
    if (document.getElementById('realtime-section')) {
        window.realtimeController = new RealtimePoseController();
    }
});
