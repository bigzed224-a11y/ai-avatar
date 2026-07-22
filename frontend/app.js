// LipSync AI - Frontend Application

// Backend API URL - Railway deployment
const API_BASE = 'https://ai-avatar-staging.up.railway.app';

// State
let state = {
    uploadedFileId: null,
    currentVideoId: null,
    selectedVoice: 'aria',
    isProcessing: false,
    voices: {}
};

// DOM Elements
const el = {
    dropZone: document.getElementById('drop-zone'),
    photoInput: document.getElementById('photo-input'),
    previewContainer: document.getElementById('preview-container'),
    photoPreview: document.getElementById('photo-preview'),
    photoName: document.getElementById('photo-name'),
    changePhotoBtn: document.getElementById('change-photo-btn'),
    voiceOptions: document.getElementById('voice-options'),
    textInput: document.getElementById('text-input'),
    charCount: document.getElementById('char-count'),
    speakBtn: document.getElementById('speak-btn'),
    loading: document.getElementById('loading'),
    loadingText: document.getElementById('loading-text'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    resultContainer: document.getElementById('result-container'),
    resultVideo: document.getElementById('result-video'),
    downloadBtn: document.getElementById('download-btn'),
    newVideoBtn: document.getElementById('new-video-btn'),
    historyContainer: document.getElementById('history-container'),
    errorToast: document.getElementById('error-toast'),
    errorMessage: document.getElementById('error-message'),
    statusBar: document.querySelector('.status-text')
};

// Initialize
function init() {
    setupEventListeners();
    loadVoices();
    loadHistory();
    checkBackend();
    setupMobileMenu();
    setupThemeToggle();
    setupRemovePhoto();
}

function setupMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    if (menuBtn && navLinks) {
        menuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('show');
        });
        // Close menu when clicking a link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => navLinks.classList.remove('show'));
        });
    }
}

function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('theme') || 'light';

    // Apply saved theme
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

function setupEventListeners() {
    el.dropZone.addEventListener('click', () => el.photoInput.click());
    el.dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        el.dropZone.classList.add('dragover');
    });
    el.dropZone.addEventListener('dragleave', () => el.dropZone.classList.remove('dragover'));
    el.dropZone.addEventListener('drop', handleDrop);
    el.photoInput.addEventListener('change', e => {
        if (e.target.files[0]) validateAndUpload(e.target.files[0]);
    });
    el.changePhotoBtn.addEventListener('click', () => {
        el.photoInput.value = '';
        el.photoInput.click();
    });
    el.textInput.addEventListener('input', handleTextInput);
    el.speakBtn.addEventListener('click', handleGenerate);
    el.downloadBtn.addEventListener('click', handleDownload);
    el.newVideoBtn.addEventListener('click', handleNewVideo);
}

function handleDrop(e) {
    e.preventDefault();
    el.dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) validateAndUpload(file);
}

function validateAndUpload(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Please upload a JPG, PNG, or WebP image');
        return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('Image must be under 10MB');
        return;
    }

    uploadPhoto(file);
}

// Upload Photo
async function uploadPhoto(file) {
    const uploadProgress = document.getElementById('upload-progress');
    const uploadStatusText = document.getElementById('upload-status-text');
    const dropZone = document.getElementById('drop-zone');

    // Show progress
    uploadProgress.classList.remove('hidden');
    dropZone.classList.add('hidden');
    uploadStatusText.textContent = 'Preparing upload...';
    setStatus('Uploading photo...');

    // Preview image locally first
    const previewUrl = URL.createObjectURL(file);
    el.photoPreview.src = previewUrl;
    el.photoName.textContent = file.name;

    // Show file details
    const sizeKB = (file.size / 1024).toFixed(1);
    const details = document.getElementById('photo-details');
    if (details) {
        details.textContent = `${sizeKB}KB  ${file.type.split('/')[1].toUpperCase()}`;
    }

    // Detect face in preview
    detectFaceInPreview(previewUrl);

    const formData = new FormData();
    formData.append('file', file);

    try {
        uploadStatusText.textContent = 'Uploading to server...';

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await response.json();
        state.uploadedFileId = data.file_id;

        uploadStatusText.textContent = 'Upload complete!';
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            el.previewContainer.classList.remove('hidden');
            el.dropZone.classList.add('hidden');

            document.getElementById('text-section').classList.add('active');
            document.getElementById('upload-section').classList.add('completed');

            updateGenerateButton();
            setStatus('Photo uploaded');
        }, 500);
    } catch (error) {
        uploadProgress.classList.add('hidden');
        dropZone.classList.remove('hidden');
        showError(error.message);
    }
}

function detectFaceInPreview(imageUrl) {
    const img = new Image();
    img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 100;
        canvas.height = 100;
        ctx.drawImage(img, 0, 0, 100, 100);
        const data = ctx.getImageData(0, 0, 100, 100).data;

        // Simple skin color detection
        let skinPixels = 0;
        for (let i = 0; i < data.length; i += 16) {
            const r = data[i], g = data[i+1], b = data[i+2];
            if (r > 100 && g > 60 && b > 40 && r > g && r > b && (r - g) > 15) {
                skinPixels++;
            }
        }

        const indicator = document.getElementById('face-indicator');
        if (skinPixels > 50) {
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    };
    img.src = imageUrl;
}

// Remove photo handler
function setupRemovePhoto() {
    const removeBtn = document.getElementById('remove-photo-btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            state.uploadedFileId = null;
            el.photoPreview.src = '';
            el.photoName.textContent = '';
            el.previewContainer.classList.add('hidden');
            el.dropZone.classList.remove('hidden');
            document.getElementById('text-section').classList.remove('active');
            document.getElementById('upload-section').classList.remove('completed');
            document.getElementById('face-indicator').style.display = 'none';
            updateGenerateButton();
            setStatus('Ready');
        });
    }
}

// Load Voices
async function loadVoices() {
    try {
        const response = await fetch(`${API_BASE}/api/voices`);
        const data = await response.json();
        state.voices = data.voices;
        renderVoiceOptions();
    } catch (error) {
        console.error('Failed to load voices:', error);
    }
}

function renderVoiceOptions() {
    el.voiceOptions.innerHTML = Object.entries(state.voices).map(([key, voice]) => `
        <button class="voice-btn ${key === state.selectedVoice ? 'selected' : ''}" data-voice="${key}">
            <span class="voice-name">${voice.name.split(' ')[0]}</span>
            <span class="voice-gender">${voice.gender === 'female' ? '\u2640' : '\u2642'}</span>
        </button>
    `).join('');

    el.voiceOptions.querySelectorAll('.voice-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            el.voiceOptions.querySelectorAll('.voice-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            state.selectedVoice = btn.dataset.voice;
        });
    });
}

// Text Input
function handleTextInput() {
    const len = el.textInput.value.length;
    el.charCount.textContent = len;
    el.charCount.style.color = len > 4500 ? '#ef4444' : len > 4000 ? '#f59e0b' : '';
    updateGenerateButton();
}

function updateGenerateButton() {
    el.speakBtn.disabled = !state.uploadedFileId || !el.textInput.value.trim() || state.isProcessing;
}

// Generate
async function handleGenerate() {
    if (state.isProcessing) return;

    const text = el.textInput.value.trim();
    if (!text || !state.uploadedFileId) return;

    state.isProcessing = true;
    updateGenerateButton();

    el.loading.classList.remove('hidden');
    el.resultContainer.classList.add('hidden');
    document.getElementById('result-section').classList.add('active');

    // Progress stages
    const stages = [
        { progress: 15, text: 'Initializing TTS engine...', duration: 800, stage: 'tts' },
        { progress: 35, text: 'Generating speech audio...', duration: 1500, stage: 'tts' },
        { progress: 55, text: 'Analyzing audio for lip sync...', duration: 1200, stage: 'analyze' },
        { progress: 75, text: 'Generating face animation...', duration: 2000, stage: 'animate' },
        { progress: 90, text: 'Rendering video frames...', duration: 1500, stage: 'render' },
        { progress: 95, text: 'Encoding final video...', duration: 1000, stage: 'render' },
    ];

    let currentStage = 0;
    let progress = 0;
    const startTime = Date.now();
    const progressTime = document.getElementById('progress-time');

    // Reset stage indicators
    document.querySelectorAll('.stage').forEach(s => {
        s.classList.remove('active', 'completed');
    });

    function updateStageIndicators(stageName) {
        const stageOrder = ['tts', 'analyze', 'animate', 'render'];
        const currentIdx = stageOrder.indexOf(stageName);

        document.querySelectorAll('.stage').forEach(s => {
            const sName = s.dataset.stage;
            const sIdx = stageOrder.indexOf(sName);
            s.classList.remove('active', 'completed');
            if (sIdx < currentIdx) s.classList.add('completed');
            else if (sIdx === currentIdx) s.classList.add('active');
        });
    }

    // Animate through stages
    const progressInterval = setInterval(() => {
        // Update elapsed time
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        progressTime.textContent = `${elapsed}s`;

        if (currentStage < stages.length) {
            const stage = stages[currentStage];
            const stageStart = stages.slice(0, currentStage).reduce((sum, s) => sum + s.duration, 0);

            if (Date.now() - startTime > stageStart + stage.duration) {
                currentStage++;
                if (currentStage < stages.length) {
                    el.loadingText.textContent = stages[currentStage].text;
                    updateProgress(stages[currentStage].progress);
                    updateStageIndicators(stages[currentStage].stage);
                }
            } else {
                // Smooth interpolation within stage
                const stageProgress = (Date.now() - startTime - stageStart) / stage.duration;
                const prevProgress = currentStage > 0 ? stages[currentStage - 1].progress : 0;
                const smoothProgress = prevProgress + (stage.progress - prevProgress) * Math.min(1, stageProgress);
                updateProgress(smoothProgress);
                updateStageIndicators(stage.stage);
            }
        }
    }, 50);

    try {
        setStatus('Generating video...');
        el.loadingText.textContent = stages[0].text;
        updateProgress(stages[0].progress);

        const response = await fetch(
            `${API_BASE}/api/speak?text=${encodeURIComponent(text)}&file_id=${state.uploadedFileId}&voice=${state.selectedVoice}`,
            { method: 'POST' }
        );

        clearInterval(progressInterval);

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Generation failed');
        }

        const data = await response.json();
        state.currentVideoId = data.video_id;

        updateProgress(100);
        el.loadingText.textContent = 'Video ready!';
        el.progressText.textContent = '100%';

        setTimeout(() => {
            el.loading.classList.add('hidden');
            el.resultContainer.classList.remove('hidden');
            el.resultVideo.src = `${API_BASE}${data.video_url}`;
            document.getElementById('result-section').classList.add('completed');
            setStatus('Video generated!');
            loadHistory();
        }, 600);

    } catch (error) {
        clearInterval(progressInterval);
        el.loading.classList.add('hidden');
        showError(error.message);
    } finally {
        state.isProcessing = false;
        updateGenerateButton();
    }
}

function updateProgress(percent) {
    const rounded = Math.min(100, Math.round(percent));
    el.progressFill.style.width = `${rounded}%`;
    el.progressText.textContent = `${rounded}%`;
}

// History
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/history?limit=5`);
        const data = await response.json();
        renderHistory(data.history);
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function renderHistory(history) {
    if (!history || history.length === 0) {
        el.historyContainer.innerHTML = '<p class="empty-history">No videos generated yet</p>';
        return;
    }

    el.historyContainer.innerHTML = `<div class="history-list">${history.map(item => `
        <div class="history-item">
            <div class="history-thumb">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
            </div>
            <div class="history-info">
                <div class="history-text">${escapeHtml(item.text || 'No text')}</div>
                <div class="history-date">${new Date(item.created_at * 1000).toLocaleString()}</div>
            </div>
            <div class="history-actions">
                <button class="btn btn-secondary btn-sm" onclick="playHistoryVideo('${item.video_id}')">Play</button>
                <button class="btn btn-secondary btn-sm" onclick="downloadHistoryVideo('${item.video_id}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </button>
            </div>
        </div>
    `).join('')}</div>`;
}

function playHistoryVideo(videoId) {
    state.currentVideoId = videoId;
    el.resultContainer.classList.remove('hidden');
    el.loading.classList.add('hidden');
    el.resultVideo.src = `${API_BASE}/api/video/${videoId}`;
    document.getElementById('result-section').classList.add('active');
    document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
}

function downloadHistoryVideo(videoId) {
    const link = document.createElement('a');
    link.href = `${API_BASE}/api/video/${videoId}`;
    link.download = `avatar_${videoId.slice(0, 8)}.mp4`;
    link.click();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Download & Reset
function handleDownload() {
    if (state.currentVideoId) downloadHistoryVideo(state.currentVideoId);
}

function handleNewVideo() {
    el.resultContainer.classList.add('hidden');
    el.resultVideo.src = '';
    el.textInput.value = '';
    el.charCount.textContent = '0';
    document.getElementById('result-section').classList.remove('active', 'completed');
    el.textInput.focus();
    updateGenerateButton();
}

// Utils
function showError(message) {
    el.errorMessage.textContent = message;
    el.errorToast.classList.remove('hidden');
    setTimeout(hideError, 5000);
}

function hideError() {
    el.errorToast.classList.add('hidden');
}

function setStatus(text) {
    el.statusBar.textContent = text;
}

window.hideError = hideError;

async function checkBackend() {
    try {
        const response = await fetch(`${API_BASE}/`);
        const data = await response.json();
        console.log('Backend:', data);
        setStatus('Connected');
    } catch (error) {
        setStatus('Server not available');
        showError('Cannot connect to the server. Please try again later.');
    }
}

// Start the app
init();
