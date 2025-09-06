/**
 * Smart Attendance System - Camera Management JavaScript
 * Handles camera access, photo capture, and face detection
 */

// Global camera variables
let currentStream = null;
let currentVideo = null;
let isCameraActive = false;
let cameraConstraints = {
    video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
    }
};

// Initialize camera functionality
document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('camera-page')) {
        initializeCameraPage();
    }
});

// Initialize camera page
function initializeCameraPage() {
    setupCameraEventListeners();
    checkCameraSupport();
}

// Setup camera event listeners
function setupCameraEventListeners() {
    // Camera control buttons
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('start-camera-btn')) {
            startCamera();
        }
        
        if (event.target.classList.contains('stop-camera-btn')) {
            stopCamera();
        }
        
        if (event.target.classList.contains('capture-photo-btn')) {
            capturePhoto();
        }
        
        if (event.target.classList.contains('switch-camera-btn')) {
            switchCamera();
        }
    });
    
    // File input for manual photo upload
    const photoInput = document.getElementById('attendancePhoto');
    if (photoInput) {
        photoInput.addEventListener('change', handlePhotoUpload);
    }
}

// Check camera support
function checkCameraSupport() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showCameraError('Camera not supported on this device');
        return false;
    }
    return true;
}

// Start camera
async function startCamera(videoElementId = 'attendanceCamera') {
    if (!checkCameraSupport()) return;
    
    const videoElement = document.getElementById(videoElementId);
    if (!videoElement) {
        showNotification('Camera element not found', 'error');
        return;
    }
    
    try {
        showNotification('Starting camera...', 'info');
        
        // Stop existing stream if any
        if (currentStream) {
            stopCamera();
        }
        
        // Get user media
        currentStream = await navigator.mediaDevices.getUserMedia(cameraConstraints);
        currentVideo = videoElement;
        
        // Set video source
        videoElement.srcObject = currentStream;
        isCameraActive = true;
        
        // Show camera controls
        showCameraControls();
        
        // Update camera info
        updateCameraInfo();
        
        showNotification('Camera started successfully', 'success');
        
    } catch (error) {
        console.error('Error starting camera:', error);
        handleCameraError(error);
    }
}

// Stop camera
function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => {
            track.stop();
        });
        currentStream = null;
    }
    
    if (currentVideo) {
        currentVideo.srcObject = null;
        currentVideo = null;
    }
    
    isCameraActive = false;
    hideCameraControls();
    
    showNotification('Camera stopped', 'info');
}

// Capture photo
function capturePhoto() {
    if (!isCameraActive || !currentVideo) {
        showNotification('Camera not active', 'warning');
        return;
    }
    
    try {
        // Create canvas element
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        
        // Set canvas dimensions to match video
        canvas.width = currentVideo.videoWidth;
        canvas.height = currentVideo.videoHeight;
        
        // Draw video frame to canvas
        context.drawImage(currentVideo, 0, 0, canvas.width, canvas.height);
        
        // Convert to blob
        canvas.toBlob(async (blob) => {
            if (blob) {
                // Create file from blob
                const file = new File([blob], 'attendance_photo.jpg', {
                    type: 'image/jpeg'
                });
                
                // Process the photo
                await processCapturedPhoto(file);
            }
        }, 'image/jpeg', 0.8);
        
    } catch (error) {
        console.error('Error capturing photo:', error);
        showNotification('Error capturing photo', 'error');
    }
}

// Process captured photo
async function processCapturedPhoto(photoFile) {
    const classId = getCurrentClassId();
    if (!classId) {
        showNotification('Class ID not found', 'error');
        return;
    }
    
    // Show photo preview
    showPhotoPreview(photoFile);
    
    // Process attendance
    if (typeof processAttendancePhoto === 'function') {
        await processAttendancePhoto(photoFile, classId);
    } else {
        // Fallback: upload photo manually
        await uploadAttendancePhoto(photoFile, classId);
    }
}

// Upload attendance photo
async function uploadAttendancePhoto(photoFile, classId) {
    const formData = new FormData();
    formData.append('attendance_photo', photoFile);
    formData.append('class_id', classId);
    
    try {
        showNotification('Uploading photo...', 'info');
        
        const response = await fetch('/api/process-attendance', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Photo uploaded successfully', 'success');
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Error uploading photo:', error);
        showNotification('Error uploading photo', 'error');
    }
}

// Show photo preview
function showPhotoPreview(photoFile) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const previewContainer = document.getElementById('imagePreview');
        if (previewContainer) {
            previewContainer.innerHTML = `
                <div class="mt-3">
                    <h6>Captured Photo:</h6>
                    <img src="${e.target.result}" class="img-fluid rounded" alt="Captured Photo" style="max-height: 300px;">
                </div>
            `;
            previewContainer.style.display = 'block';
        }
    };
    reader.readAsDataURL(photoFile);
}

// Handle photo upload
function handlePhotoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showNotification('Please select an image file', 'warning');
        return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showNotification('File size too large. Please select a smaller image.', 'warning');
        return;
    }
    
    // Show preview
    showPhotoPreview(file);
    
    // Auto-process if form is submitted
    const form = event.target.closest('form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const classId = getCurrentClassId();
            if (classId) {
                await processCapturedPhoto(file);
            }
        });
    }
}

// Switch camera (front/back)
async function switchCamera() {
    if (!isCameraActive) {
        showNotification('Camera not active', 'warning');
        return;
    }
    
    try {
        // Toggle facing mode
        cameraConstraints.video.facingMode = 
            cameraConstraints.video.facingMode === 'user' ? 'environment' : 'user';
        
        // Restart camera with new constraints
        stopCamera();
        await startCamera();
        
        showNotification('Camera switched', 'info');
    } catch (error) {
        console.error('Error switching camera:', error);
        showNotification('Error switching camera', 'error');
    }
}

// Show camera controls
function showCameraControls() {
    const controlsContainer = document.getElementById('cameraControls');
    if (controlsContainer) {
        controlsContainer.style.display = 'block';
    }
}

// Hide camera controls
function hideCameraControls() {
    const controlsContainer = document.getElementById('cameraControls');
    if (controlsContainer) {
        controlsContainer.style.display = 'none';
    }
}

// Update camera info
function updateCameraInfo() {
    const infoContainer = document.getElementById('cameraInfo');
    if (infoContainer && currentVideo) {
        infoContainer.innerHTML = `
            <div class="alert alert-info">
                <small>
                    <i class="fas fa-info-circle"></i>
                    Camera active • Resolution: ${currentVideo.videoWidth}x${currentVideo.videoHeight}
                </small>
            </div>
        `;
    }
}

// Handle camera errors
function handleCameraError(error) {
    let errorMessage = 'Camera error occurred';
    
    switch (error.name) {
        case 'NotAllowedError':
            errorMessage = 'Camera access denied. Please allow camera permissions.';
            break;
        case 'NotFoundError':
            errorMessage = 'No camera found on this device.';
            break;
        case 'NotReadableError':
            errorMessage = 'Camera is being used by another application.';
            break;
        case 'OverconstrainedError':
            errorMessage = 'Camera constraints cannot be satisfied.';
            break;
        case 'SecurityError':
            errorMessage = 'Camera access blocked due to security restrictions.';
            break;
        default:
            errorMessage = `Camera error: ${error.message}`;
    }
    
    showCameraError(errorMessage);
}

// Show camera error
function showCameraError(message) {
    const cameraContainer = document.getElementById('cameraContainer');
    if (cameraContainer) {
        cameraContainer.innerHTML = `
            <div class="camera-error">
                <i class="fas fa-video-slash fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Camera Unavailable</h5>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary" onclick="startCamera()">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            </div>
        `;
    }
    
    showNotification(message, 'error');
}

// Get current class ID
function getCurrentClassId() {
    const classIdElement = document.getElementById('classId');
    return classIdElement ? classIdElement.value : null;
}

// Initialize camera with specific element
function initializeCamera(videoElementId) {
    return startCamera(videoElementId);
}

// Check if camera is active
function isCameraRunning() {
    return isCameraActive;
}

// Get camera stream
function getCameraStream() {
    return currentStream;
}

// Export functions for global use
window.startCamera = startCamera;
window.stopCamera = stopCamera;
window.capturePhoto = capturePhoto;
window.switchCamera = switchCamera;
window.initializeCamera = initializeCamera;
window.isCameraRunning = isCameraRunning;
window.getCameraStream = getCameraStream;