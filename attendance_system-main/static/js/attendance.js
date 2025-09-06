/**
 * Smart Attendance System - Attendance Management JavaScript
 * Handles attendance-related functionality
 */

// Global attendance variables
let currentAttendanceSession = null;
let attendanceData = {
    present: [],
    absent: [],
    total: 0
};

// Initialize attendance page
document.addEventListener('DOMContentLoaded', function() {
    if (document.body.classList.contains('attendance-page')) {
        initializeAttendancePage();
    }
});

// Initialize attendance page
function initializeAttendancePage() {
    loadAttendanceSummary();
    setupAttendanceEventListeners();
    
    // Auto-refresh attendance data every 30 seconds
    setInterval(loadAttendanceSummary, 30000);
}

// Setup attendance event listeners
function setupAttendanceEventListeners() {
    // Manual attendance marking
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('mark-present-btn')) {
            const studentId = event.target.getAttribute('data-student-id');
            markStudentAttendance(studentId, 'present');
        }
        
        if (event.target.classList.contains('mark-absent-btn')) {
            const studentId = event.target.getAttribute('data-student-id');
            markStudentAttendance(studentId, 'absent');
        }
    });
    
    // Attendance filters
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterAttendanceByStatus);
    }
    
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', searchAttendance);
    }
}

// Load attendance summary
async function loadAttendanceSummary() {
    const classId = getCurrentClassId();
    if (!classId) return;
    
    try {
        const data = await apiCall(`/api/attendance-summary/${classId}`);
        
        if (data.success) {
            updateAttendanceSummary(data);
            updateAttendanceStatistics(data);
        }
    } catch (error) {
        console.error('Error loading attendance summary:', error);
    }
}

// Update attendance summary display
function updateAttendanceSummary(data) {
    const container = document.getElementById('attendanceSummary');
    if (!container) return;
    
    if (!data.present_students || data.present_students.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-chart-bar fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No attendance data yet</h5>
                <p class="text-muted">Take attendance using face recognition or QR scanning</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="row mb-3">
            <div class="col-md-4">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h5>Present</h5>
                        <h3>${data.total_present}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-danger text-white">
                    <div class="card-body text-center">
                        <h5>Absent</h5>
                        <h3>${data.total_absent}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h5>Total</h5>
                        <h3>${data.total_present + data.total_absent}</h3>
                    </div>
                </div>
            </div>
        </div>
        <div class="table-responsive">
            <table class="table table-bordered" id="attendanceTable">
                <thead>
                    <tr>
                        <th>Student ID</th>
                        <th>Name</th>
                        <th>Roll No</th>
                        <th>Status</th>
                        <th>Time</th>
                        <th>Method</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // Add present students
    data.present_students.forEach(student => {
        html += `
            <tr class="table-success">
                <td>${student.student_id}</td>
                <td>${student.full_name}</td>
                <td>${student.roll_number}</td>
                <td><span class="badge badge-success">Present</span></td>
                <td>${student.time_marked ? formatTime(student.time_marked) : '-'}</td>
                <td>${student.method || 'Face Recognition'}</td>
            </tr>
        `;
    });
    
    // Add absent students
    data.absent_students.forEach(student => {
        html += `
            <tr class="table-danger">
                <td>${student.student_id}</td>
                <td>${student.full_name}</td>
                <td>${student.roll_number}</td>
                <td><span class="badge badge-danger">Absent</span></td>
                <td>-</td>
                <td>-</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// Update attendance statistics
function updateAttendanceStatistics(data) {
    const presentElement = document.getElementById('presentToday');
    const absentElement = document.getElementById('absentToday');
    const totalElement = document.getElementById('totalToday');
    const percentElement = document.getElementById('attendancePercent');
    
    if (presentElement) presentElement.textContent = data.total_present;
    if (absentElement) absentElement.textContent = data.total_absent;
    if (totalElement) totalElement.textContent = data.total_present + data.total_absent;
    
    if (percentElement) {
        const total = data.total_present + data.total_absent;
        const percentage = total > 0 ? ((data.total_present / total) * 100).toFixed(1) : 0;
        percentElement.textContent = percentage + '%';
    }
}

// Mark student attendance
async function markStudentAttendance(studentId, status) {
    const classId = getCurrentClassId();
    if (!classId) {
        showNotification('Class ID not found', 'error');
        return;
    }
    
    try {
        const data = await apiCall('/api/attendance', {
            method: 'POST',
            body: JSON.stringify({
                student_id: studentId,
                class_id: classId,
                status: status,
                method: 'manual'
            })
        });
        
        if (data.success) {
            showNotification(`Student marked as ${status}`, 'success');
            loadAttendanceSummary(); // Refresh data
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Error marking attendance:', error);
        showNotification('Error marking attendance', 'error');
    }
}

// Filter attendance by status
function filterAttendanceByStatus() {
    const status = document.getElementById('statusFilter').value;
    const rows = document.querySelectorAll('#attendanceTable tbody tr');
    
    rows.forEach(row => {
        if (!status) {
            row.style.display = '';
        } else {
            const isPresent = row.classList.contains('table-success');
            const isAbsent = row.classList.contains('table-danger');
            
            const shouldShow = (status === 'present' && isPresent) || 
                             (status === 'absent' && isAbsent);
            
            row.style.display = shouldShow ? '' : 'none';
        }
    });
}

// Search attendance
function searchAttendance() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#attendanceTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// Get current class ID
function getCurrentClassId() {
    const classIdElement = document.getElementById('classId');
    return classIdElement ? classIdElement.value : null;
}

// Process attendance photo
async function processAttendancePhoto(photoFile, classId) {
    const formData = new FormData();
    formData.append('attendance_photo', photoFile);
    formData.append('class_id', classId);
    
    try {
        showNotification('Processing photo...', 'info');
        
        const response = await fetch('/api/process-attendance', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Attendance processed successfully! ${data.recognized_count} students recognized.`, 'success');
            loadAttendanceSummary(); // Refresh data
            
            // Show recognition results
            if (data.recognition_results) {
                showRecognitionResults(data.recognition_results);
            }
        } else {
            showNotification(data.error, 'error');
        }
    } catch (error) {
        console.error('Error processing attendance photo:', error);
        showNotification('Error processing photo', 'error');
    }
}

// Show recognition results
function showRecognitionResults(results) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'recognitionResultsModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Face Recognition Results</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Recognized Students</h6>
                            <ul class="list-group">
                                ${results.recognized.map(student => `
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        ${student.name}
                                        <span class="badge badge-success">Recognized</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Unrecognized Faces</h6>
                            <ul class="list-group">
                                ${results.unrecognized.map((face, index) => `
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        Face ${index + 1}
                                        <span class="badge badge-warning">Unknown</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    modal.addEventListener('hidden.bs.modal', function() {
        modal.remove();
    });
}

// Export attendance data
function exportAttendanceData() {
    const classId = getCurrentClassId();
    if (!classId) {
        showNotification('Class ID not found', 'error');
        return;
    }
    
    const url = `/api/export/attendance/${classId}`;
    window.open(url, '_blank');
}

// Print attendance report
function printAttendanceReport() {
    window.print();
}

// Refresh attendance data
function refreshAttendance() {
    loadAttendanceSummary();
    showNotification('Attendance data refreshed', 'info');
}

// Export functions for global use
window.processAttendancePhoto = processAttendancePhoto;
window.markStudentAttendance = markStudentAttendance;
window.exportAttendanceData = exportAttendanceData;
window.printAttendanceReport = printAttendanceReport;
window.refreshAttendance = refreshAttendance;