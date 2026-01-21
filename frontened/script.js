// Traffic Detection Frontend JavaScript

// DOM Elements
const videoUpload = document.getElementById('videoUpload');
const videoPlayer = document.getElementById('videoPlayer');
const processBtn = document.getElementById('processBtn');
const resultsContainer = document.getElementById('results');
const vehicleCount = document.getElementById('vehicleCount');
const statusText = document.getElementById('status');

// Handle video file upload
function handleVideoUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const videoURL = URL.createObjectURL(file);
        videoPlayer.src = videoURL;
        videoPlayer.style.display = 'block';
        processBtn.disabled = false;
        updateStatus('Video loaded. Ready to process.');
    }
}

// Process video with backend
async function processVideo() {
    if (!videoUpload.files[0]) {
        alert('Please upload a video first');
        return;
    }

    const formData = new FormData();
    formData.append('video', videoUpload.files[0]);

    updateStatus('Processing video...');
    processBtn.disabled = true;

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        displayResults(data);
        updateStatus('Processing complete!');
    } catch (error) {
        console.error('Error:', error);
        updateStatus('Error processing video. Please try again.');
    } finally {
        processBtn.disabled = false;
    }
}

// Display detection results
function displayResults(data) {
    resultsContainer.style.display = 'block';
    vehicleCount.textContent = data.vehicle_count || 0;
    
    if (data.processed_video_url) {
        videoPlayer.src = data.processed_video_url;
    }
}

// Update status message
function updateStatus(message) {
    if (statusText) {
        statusText.textContent = message;
    }
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    if (videoUpload) {
        videoUpload.addEventListener('change', handleVideoUpload);
    }
    
    if (processBtn) {
        processBtn.addEventListener('click', processVideo);
    }
});

// Real-time detection display
function updateLiveDetection(frame, detections) {
    const canvas = document.getElementById('detectionCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(frame, 0, 0, canvas.width, canvas.height);
    
    detections.forEach(detection => {
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 2;
        ctx.strokeRect(
            detection.x1,
            detection.y1,
            detection.x2 - detection.x1,
            detection.y2 - detection.y1
        );
    });
}
