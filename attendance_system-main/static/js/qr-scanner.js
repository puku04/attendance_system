/**
 * Smart Attendance System - QR Code Scanner JavaScript
 * Handles QR code scanning functionality using html5-qrcode library
 */

// Global QR scanner variables
let qrScannerManager = null;
let isQRScannerActive = false;
let currentScannerElement = null;
let scanTimeout = null;
let torchEnabled = false;

// Initialize QR scanner functionality
document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('qr-scanner-page')) {
        initializeQRScannerPage();
    }
});

// Initialize QR scanner page
function initializeQRScannerPage() {
    setupQREventListeners();
    checkQRScannerSupport();
}

// Setup QR event listeners
function setupQREventListeners() {
    // QR scanner control buttons
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('start-qr-scanner-btn')) {
            startQRScanner();
        }
        
        if (event.target.classList.contains('stop-qr-scanner-btn')) {
            stopQRScanner();
        }
        
        if (event.target.classList.contains('toggle-torch-btn')) {
            toggleTorch();
        }
        
        if (event.target.classList.contains('switch-qr-camera-btn')) {
            switchQRCamera();
        }
    });
}

// Check QR scanner support
function checkQRScannerSupport() {
    if (typeof Html5Qrcode === 'undefined') {
        showQRScannerError('QR scanner library not loaded');
        return false;
    }
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showQRScannerError('Camera not supported on this device');
        return false;
    }
    
    return true;
}

// Initialize QR scanner
function initializeQRScanner(elementId, onQRCodeDetected) {
    if (!checkQRScannerSupport()) return;
    
    currentScannerElement = document.getElementById(elementId);
    if (!currentScannerElement) {
        showNotification('QR scanner element not found', 'error');
        return;
    }
    
    try {
        qrScannerManager = new Html5Qrcode(elementId);
        
        // Store the callback function
        if (onQRCodeDetected) {
            qrScannerManager.onQRCodeDetected = onQRCodeDetected;
        }
        
        showNotification('QR scanner initialized', 'success');
        
    } catch (error) {
        console.error('Error initializing QR scanner:', error);
        showQRScannerError('Failed to initialize QR scanner');
    }
}

// Start QR scanning
async function startQRScanner() {
    if (!qrScannerManager) {
        showNotification('QR scanner not initialized', 'warning');
        return;
    }
    
    if (isQRScannerActive) {
        showNotification('QR scanner already active', 'info');
        return;
    }
    
    try {
        showNotification('Starting QR scanner...', 'info');
        
        // Get available cameras
        const cameras = await Html5Qrcode.getCameras();
        if (cameras.length === 0) {
            throw new Error('No cameras found');
        }
        
        // Use first available camera
        const cameraId = cameras[0].id;
        
        // Start scanning
        await qrScannerManager.start(
            cameraId,
            {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0
            },
            onQRCodeScanned,
            onQRScannerError
        );
        
        isQRScannerActive = true;
        updateQRScannerStatus('active');
        
        showNotification('QR scanner started successfully', 'success');
        
    } catch (error) {
        console.error('Error starting QR scanner:', error);
        handleQRScannerError(error);
    }
}

// Stop QR scanning
async function stopQRScanner() {
    if (!qrScannerManager || !isQRScannerActive) {
        showNotification('QR scanner not active', 'warning');
        return;
    }
    
    try {
        await qrScannerManager.stop();
        isQRScannerActive = false;
        updateQRScannerStatus('inactive');
        
        // Clear scanner element
        if (currentScannerElement) {
            currentScannerElement.innerHTML = '';
        }
        
        showNotification('QR scanner stopped', 'info');
        
    } catch (error) {
        console.error('Error stopping QR scanner:', error);
        showNotification('Error stopping QR scanner', 'error');
    }
}

// Handle QR code scanned
function onQRCodeScanned(decodedText, decodedResult) {
    console.log('QR Code detected:', decodedText);
    
    // Play success sound (if available)
    playScanSound();
    
    // Show visual feedback
    showScanFeedback(decodedText);
    
    // Process the QR code
    processQRCode(decodedText);
    
    // Set timeout to prevent multiple scans
    if (scanTimeout) {
        clearTimeout(scanTimeout);
    }
    
    scanTimeout = setTimeout(() => {
        // Resume scanning after delay
    }, 2000);
}

// Process QR code
function processQRCode(qrData) {
    try {
        // Parse QR data (assuming it's JSON)
        const data = JSON.parse(qrData);
        
        // Validate QR data structure
        if (!data.student_id) {
            throw new Error('Invalid QR code format');
        }
        
        // Call the callback function if available
        if (typeof window.onQRCodeDetected === 'function') {
            window.onQRCodeDetected(qrData);
        } else {
            // Default processing
            showNotification(`QR Code scanned: ${data.student_id}`, 'success');
        }
        
    } catch (error) {
        console.error('Error processing QR code:', error);
        showNotification('Invalid QR code format', 'error');
    }
}

// Show scan feedback
function showScanFeedback(qrData) {
    // Create temporary overlay
    const overlay = document.createElement('div');
    overlay.className = 'qr-scan-overlay';
    overlay.innerHTML = `
        <div class="qr-scan-feedback">
            <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
            <h5>QR Code Scanned!</h5>
            <p class="text-muted">Processing...</p>
        </div>
    `;
    
    // Style the overlay
    overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        color: white;
        text-align: center;
    `;
    
    // Add to scanner element
    if (currentScannerElement) {
        currentScannerElement.style.position = 'relative';
        currentScannerElement.appendChild(overlay);
        
        // Remove after 2 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 2000);
    }
}

// Play scan sound
function playScanSound() {
    // Create audio element for scan sound
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT');
    audio.volume = 0.3;
    audio.play().catch(e => console.log('Could not play scan sound:', e));
}

// Toggle torch/flashlight
async function toggleTorch() {
    if (!qrScannerManager || !isQRScannerActive) {
        showNotification('QR scanner not active', 'warning');
        return;
    }
    
    try {
        // Note: Torch control is not directly supported by html5-qrcode
        // This is a placeholder for future implementation
        torchEnabled = !torchEnabled;
        showNotification(`Torch ${torchEnabled ? 'enabled' : 'disabled'}`, 'info');
        
    } catch (error) {
        console.error('Error toggling torch:', error);
        showNotification('Error toggling torch', 'error');
    }
}

// Switch QR camera
async function switchQRCamera() {
    if (!qrScannerManager || !isQRScannerActive) {
        showNotification('QR scanner not active', 'warning');
        return;
    }
    
    try {
        // Get available cameras
        const cameras = await Html5Qrcode.getCameras();
        if (cameras.length < 2) {
            showNotification('Only one camera available', 'info');
            return;
        }
        
        // Stop current scanner
        await stopQRScanner();
        
        // Start with different camera
        await startQRScanner();
        
        showNotification('Camera switched', 'info');
        
    } catch (error) {
        console.error('Error switching camera:', error);
        showNotification('Error switching camera', 'error');
    }
}

// Set scan timeout
function setScanTimeout(seconds) {
    if (scanTimeout) {
        clearTimeout(scanTimeout);
    }
    
    scanTimeout = setTimeout(() => {
        if (isQRScannerActive) {
            showNotification('Scan timeout reached', 'warning');
            // Optionally stop scanner
            // stopQRScanner();
        }
    }, seconds * 1000);
    
    showNotification(`Scan timeout set to ${seconds} seconds`, 'info');
}

// Update QR scanner status
function updateQRScannerStatus(status) {
    const statusElement = document.getElementById('qrScannerStatus');
    if (statusElement) {
        statusElement.innerHTML = `
            <div class="alert alert-${status === 'active' ? 'success' : 'secondary'}">
                <i class="fas fa-qrcode me-2"></i>
                QR Scanner: ${status === 'active' ? 'Active' : 'Inactive'}
            </div>
        `;
    }
}

// Handle QR scanner errors
function onQRScannerError(error) {
    console.error('QR Scanner error:', error);
    
    // Don't show error for every failed scan attempt
    if (error.includes('No QR code found')) {
        return;
    }
    
    showNotification('QR scanner error: ' + error, 'error');
}

// Show QR scanner error
function showQRScannerError(message) {
    const scannerContainer = document.getElementById('qrScanner');
    if (scannerContainer) {
        scannerContainer.innerHTML = `
            <div class="qr-scanner-error text-center py-5">
                <i class="fas fa-qrcode fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">QR Scanner Unavailable</h5>
                <p class="text-muted">${message}</p>
                <button class="btn btn-primary" onclick="startQRScanner()">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            </div>
        `;
    }
    
    showNotification(message, 'error');
}

// Handle QR scanner errors
function handleQRScannerError(error) {
    let errorMessage = 'QR scanner error occurred';
    
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
            errorMessage = `QR scanner error: ${error.message}`;
    }
    
    showQRScannerError(errorMessage);
}

// Cleanup QR scanner
function cleanupQRScanner() {
    if (qrScannerManager && isQRScannerActive) {
        stopQRScanner();
    }
    
    if (scanTimeout) {
        clearTimeout(scanTimeout);
        scanTimeout = null;
    }
}

// Export functions for global use
window.initializeQRScanner = initializeQRScanner;
window.startQRScanner = startQRScanner;
window.stopQRScanner = stopQRScanner;
window.toggleTorch = toggleTorch;
window.switchQRCamera = switchQRCamera;
window.setScanTimeout = setScanTimeout;
window.cleanupQRScanner = cleanupQRScanner;

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupQRScanner);