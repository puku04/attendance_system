/**
 * Smart Attendance System - Main JavaScript Functions
 * Global utility functions and UI interactions
 */

// Global variables
let currentUser = null;
let notifications = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    startRealTimeClock();
});

// Initialize application
function initializeApp() {
    // Check if user is logged in
    if (document.body.classList.contains('logged-in')) {
        loadUserData();
    }
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize notifications
    initializeNotifications();
    
    // Setup auto-save for forms
    setupAutoSave();
}

// Setup event listeners
function setupEventListeners() {
    // Form validation
    document.addEventListener('submit', handleFormSubmit);
    
    // Real-time search
    document.addEventListener('input', handleRealTimeSearch);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Window events
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOfflineStatus);
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const notification = {
        id: Date.now(),
        message: message,
        type: type,
        duration: duration,
        timestamp: new Date()
    };
    
    notifications.push(notification);
    displayNotification(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        removeNotification(notification.id);
    }, duration);
}

// Display notification
function displayNotification(notification) {
    const container = getNotificationContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${notification.type} alert-dismissible fade show notification-item`;
    alertDiv.setAttribute('data-notification-id', notification.id);
    alertDiv.innerHTML = `
        <i class="fas fa-${getNotificationIcon(notification.type)} me-2"></i>
        ${notification.message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.appendChild(alertDiv);
    
    // Animate in
    setTimeout(() => {
        alertDiv.classList.add('show');
    }, 100);
}

// Remove notification
function removeNotification(id) {
    const notification = document.querySelector(`[data-notification-id="${id}"]`);
    if (notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
    
    // Remove from array
    notifications = notifications.filter(n => n.id !== id);
}

// Get notification container
function getNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

// Get notification icon
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// API call function
async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        showNotification('Network error. Please check your connection.', 'error');
        throw error;
    }
}

// Form validation
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Handle form submit
function handleFormSubmit(event) {
    const form = event.target;
    
    if (form.classList.contains('needs-validation')) {
        if (!validateForm(form)) {
            event.preventDefault();
            event.stopPropagation();
            showNotification('Please fill all required fields', 'warning');
        }
    }
    
    form.classList.add('was-validated');
}

// Real-time search
function handleRealTimeSearch(event) {
    const input = event.target;
    
    if (input.classList.contains('search-input')) {
        const searchTerm = input.value.toLowerCase();
        const targetTable = input.getAttribute('data-target');
        
        if (targetTable) {
            filterTable(targetTable, searchTerm);
        }
    }
}

// Filter table
function filterTable(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const shouldShow = text.includes(searchTerm);
        row.style.display = shouldShow ? '' : 'none';
    });
}

// Keyboard shortcuts
function handleKeyboardShortcuts(event) {
    // Ctrl + S: Save form
    if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        const form = document.querySelector('form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Ctrl + K: Focus search
    if (event.ctrlKey && event.key === 'k') {
        event.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape: Close modals
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
}

// Real-time clock
function startRealTimeClock() {
    const clockElement = document.getElementById('realTimeClock');
    if (!clockElement) return;
    
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour12: true,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        const dateString = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        clockElement.innerHTML = `
            <div>${timeString}</div>
            <small>${dateString}</small>
        `;
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize notifications
function initializeNotifications() {
    // Check for flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        const type = alert.classList.contains('alert-danger') ? 'error' : 
                    alert.classList.contains('alert-warning') ? 'warning' :
                    alert.classList.contains('alert-success') ? 'success' : 'info';
        
        showNotification(alert.textContent.trim(), type);
    });
}

// Setup auto-save
function setupAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                saveFormData(form);
            }, 1000));
        });
    });
}

// Save form data
function saveFormData(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    localStorage.setItem(`form_${form.id}`, JSON.stringify(data));
}

// Load form data
function loadFormData(form) {
    const savedData = localStorage.getItem(`form_${form.id}`);
    if (savedData) {
        const data = JSON.parse(savedData);
        
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Loading states
function showLoading(element) {
    if (element.tagName === 'BUTTON') {
        element.disabled = true;
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    } else {
        element.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div><p class="mt-2">Loading...</p></div>';
    }
}

function hideLoading(element, originalText = 'Submit') {
    if (element.tagName === 'BUTTON') {
        element.disabled = false;
        element.innerHTML = originalText;
    }
}

// Handle before unload
function handleBeforeUnload(event) {
    const forms = document.querySelectorAll('form[data-autosave]');
    const hasUnsavedChanges = Array.from(forms).some(form => {
        const formData = new FormData(form);
        const currentData = Object.fromEntries(formData);
        const savedData = localStorage.getItem(`form_${form.id}`);
        
        if (savedData) {
            const saved = JSON.parse(savedData);
            return JSON.stringify(currentData) !== JSON.stringify(saved);
        }
        return Object.keys(currentData).length > 0;
    });
    
    if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
}

// Handle online status
function handleOnlineStatus() {
    showNotification('Connection restored', 'success');
}

// Handle offline status
function handleOfflineStatus() {
    showNotification('You are offline. Some features may not work.', 'warning');
}

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-US', {
        hour12: true,
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateTime(date) {
    return `${formatDate(date)} at ${formatTime(date)}`;
}

// Export functions for global use
window.showNotification = showNotification;
window.apiCall = apiCall;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.formatDateTime = formatDateTime;