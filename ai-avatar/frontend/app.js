const API_BASE = 'http://localhost:8000';

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
}

function setupEventListeners() {
    el.dropZone.addEventListener('click', () => el.photoInput.click());
    el.dropZone.addEventListener('dragover', e => { e.preventDefault(); el.dropZone.classList.add('dragover'); });
    el.dropZone.addEventListener('dragleave', () => el.dropZone.classList.remove('dragover'));
    el.dropZone.addEventListener('drop', handleDrop);
    el.photoInput.addEventListener('change', e => { if (e.target.files[0]) uploadPhoto(e.target.files[0]); });
    el.changePhotoBtn.addEventListener('click', () => { el.photoInput.value = ''; el.photoInput.click(); });
    el.textInput.addEventListener('input', handleTextInput);
    el.speakBtn.addEventListener('click', handleGenerate);
    el.downloadBtn.addEventListener('click', handleDownload);
    el.newVideoBtn.addEventListener('click', handleNewVideo);
}

function handleDrop(e) {
    e.preventDefault();
    el.dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) uploadPhoto(file);
    else showError('Please upload an image file');
}

// Upload Photo
async function uploadPhoto(file) {
    setStatus('Uploading photo...');
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error((await response.json()).detail || 'Upload failed');
        
        const data = await response.json();
        state.uploadedFileId = data.file_id;

        el.photoPreview.src = URL.createObjectURL(file);
        el.photoName.textContent = file.name;
        el.previewContainer.classList.remove('hidden');
        el.dropZone.classList.add('hidden');
        
        document.getElementById('text-section').classList.add('active');
        document.getElementById('upload-section').classList.add('completed');
        
        updateGenerateButton();
        setStatus('Photo uploaded');
    } catch (error) {
        showError(error.message);
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
            <span class="voice-gender">${voice.gender === 'female' ? '♀' : '♂'}</span>
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
    
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 10;
            updateProgress(progress);
        }
    }, 500);
    
    try {
        setStatus('Generating video...');
        el.loadingText.textContent = 'Converting text to speech...';
        
        const response = await fetch(
            `${API_BASE}/api/speak?text=${encodeURIComponent(text)}&file_id=${state.uploadedFileId}&voice=${state.selectedVoice}`,
            { method: 'POST' }
        );

        clearInterval(progressInterval);
        
        if (!response.ok) throw new Error((await response.json()).detail || 'Generation failed');

        const data = await response.json();
        state.currentVideoId = data.video_id;
        
        updateProgress(100);
        el.loadingText.textContent = 'Done!';
        
        setTimeout(() => {
            el.loading.classList.add('hidden');
            el.resultContainer.classList.remove('hidden');
            el.resultVideo.src = `${API_BASE}${data.video_url}`;
            document.getElementById('result-section').classList.add('completed');
            setStatus('Video generated!');
            loadHistory();
        }, 500);
        
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
            <div class="history-thumb">🎬</div>
            <div class="history-info">
                <div class="history-text">${escapeHtml(item.text || 'No text')}</div>
                <div class="history-date">${new Date(item.created_at * 1000).toLocaleString()}</div>
            </div>
            <div class="history-actions">
                <button class="secondary-btn" onclick="playHistoryVideo('${item.video_id}')">Play</button>
                <button class="secondary-btn" onclick="downloadHistoryVideo('${item.video_id}')">↓</button>
            </div>
        </div>
    `).join('')}</div>`;
}

function playHistoryVideo(videoId) {
    state.currentVideoId = videoId;
    el.resultContainer.classList.remove('hidden');
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

function hideError() { el.errorToast.classList.add('hidden'); }
function setStatus(text) { el.statusBar.textContent = text; }
window.hideError = hideError;

async function checkBackend() {
    try {
        const response = await fetch(`${API_BASE}/`);
        const data = await response.json();
        console.log('Backend:', data);
        setStatus('Connected');
    } catch (error) {
        setStatus('Server not running');
        showError('Cannot connect to backend. Start with: cd backend && python main.py');
    }
}

init();
