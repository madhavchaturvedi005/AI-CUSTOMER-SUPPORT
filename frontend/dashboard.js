/**
 * Dashboard JavaScript for AI Voice Automation System
 * Handles tab switching, data fetching, charts, and form submissions
 */

// API Base URL
const API_BASE = window.location.origin;

// Chart instances
let callVolumeChart = null;
let intentChart = null;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard initializing...');
    
    // Show dashboard tab by default
    showTab('dashboard');
    
    // Initialize charts
    initializeCharts();
    
    // Load initial data
    refreshDashboard();
    
    // Set up form handlers
    setupFormHandlers();
    
    // Load configuration after a short delay to ensure forms are rendered
    setTimeout(() => {
        console.log('📝 Loading configuration...');
        loadCurrentConfiguration();
    }, 500);
    
    // Auto-refresh dashboard every 30 seconds
    setInterval(refreshDashboard, 30000);
    
    console.log('✅ Dashboard initialized!');
});

/**
 * Tab switching functionality
 */
function showTab(tabName) {
    // Hide all tab contents
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.add('hidden'));
    
    // Remove active class from all tab buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => {
        button.classList.remove('active', 'border-blue-500', 'text-blue-600');
        button.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Show selected tab content
    const selectedContent = document.getElementById(`content-${tabName}`);
    if (selectedContent) {
        selectedContent.classList.remove('hidden');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.getElementById(`tab-${tabName}`);
    if (selectedButton) {
        selectedButton.classList.remove('border-transparent', 'text-gray-500');
        selectedButton.classList.add('active', 'border-blue-500', 'text-blue-600');
    }
    
    // Load data for the selected tab
    switch(tabName) {
        case 'dashboard':
            refreshDashboard();
            break;
        case 'calls':
            refreshCalls();
            break;
        case 'leads':
            refreshLeads();
            break;
        case 'appointments':
            refreshAppointments();
            break;
        case 'config':
            loadCurrentConfiguration();
            break;
        case 'documents':
            refreshDocumentsList();
            break;
    }
}

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    // Call Volume Chart
    const callVolumeCtx = document.getElementById('callVolumeChart');
    if (callVolumeCtx) {
        callVolumeChart = new Chart(callVolumeCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Calls',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    // Intent Distribution Chart
    const intentCtx = document.getElementById('intentChart');
    if (intentCtx) {
        intentChart = new Chart(intentCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(168, 85, 247)',
                        'rgb(251, 191, 36)',
                        'rgb(239, 68, 68)',
                        'rgb(156, 163, 175)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

/**
 * Refresh dashboard statistics and charts
 */
async function refreshDashboard() {
    try {
        const response = await fetch(`${API_BASE}/api/analytics`);
        if (!response.ok) throw new Error('Failed to fetch analytics');
        
        const data = await response.json();
        
        // Update statistics cards
        document.getElementById('stat-total-calls').textContent = data.total_calls || 0;
        document.getElementById('stat-leads').textContent = data.total_leads || 0;
        document.getElementById('stat-appointments').textContent = data.total_appointments || 0;
        document.getElementById('stat-duration').textContent = `${data.avg_duration || 0}m`;
        
        // Update call volume chart
        if (callVolumeChart && data.call_volume) {
            callVolumeChart.data.labels = data.call_volume.labels;
            callVolumeChart.data.datasets[0].data = data.call_volume.data;
            callVolumeChart.update();
        }
        
        // Update intent distribution chart
        if (intentChart && data.intent_distribution) {
            intentChart.data.labels = data.intent_distribution.labels;
            intentChart.data.datasets[0].data = data.intent_distribution.data;
            intentChart.update();
        }
        
        // Update recent activity
        updateRecentActivity(data.recent_activity || []);
        
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

/**
 * Update recent activity feed
 */
function updateRecentActivity(activities) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent activity</p>';
        return;
    }
    
    container.innerHTML = activities.map(activity => `
        <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div class="flex-shrink-0">
                <i class="fas ${getActivityIcon(activity.type)} text-blue-600"></i>
            </div>
            <div class="flex-1">
                <p class="text-sm font-medium text-gray-900">${activity.title}</p>
                <p class="text-xs text-gray-500">${activity.time}</p>
            </div>
        </div>
    `).join('');
}

/**
 * Get icon for activity type
 */
function getActivityIcon(type) {
    const icons = {
        'call': 'fa-phone',
        'lead': 'fa-user-plus',
        'appointment': 'fa-calendar-check',
        'transfer': 'fa-exchange-alt'
    };
    return icons[type] || 'fa-circle';
}

/**
 * Refresh calls table
 */
async function refreshCalls() {
    try {
        const response = await fetch(`${API_BASE}/api/calls`);
        if (!response.ok) throw new Error('Failed to fetch calls');
        
        const data = await response.json();
        const tbody = document.getElementById('calls-table-body');
        
        if (!tbody) return;
        
        if (data.calls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No calls found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.calls.map(call => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${formatDateTime(call.started_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${call.caller_phone}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${formatIntent(call.intent)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${formatDuration(call.duration_seconds)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${getStatusBadge(call.status)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <button onclick="viewCallDetails('${call.id}')" class="text-blue-600 hover:text-blue-800">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error refreshing calls:', error);
    }
}

/**
 * Refresh leads table
 */
async function refreshLeads() {
    try {
        const response = await fetch(`${API_BASE}/api/leads`);
        if (!response.ok) throw new Error('Failed to fetch leads');
        
        const data = await response.json();
        const tbody = document.getElementById('leads-table-body');
        
        if (!tbody) return;
        
        if (data.leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">No leads found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.leads.map(lead => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${lead.name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.phone}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.email || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${getScoreBadge(lead.lead_score)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.budget_indication || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.timeline || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <button onclick="viewLeadDetails('${lead.id}')" class="text-blue-600 hover:text-blue-800">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error refreshing leads:', error);
    }
}

/**
 * Filter leads by score
 */
async function filterLeads(filter) {
    try {
        let url = `${API_BASE}/api/leads`;
        if (filter !== 'all') {
            url += `?filter=${filter}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch leads');
        
        const data = await response.json();
        const tbody = document.getElementById('leads-table-body');
        
        if (!tbody) return;
        
        if (data.leads.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">No leads found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.leads.map(lead => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${lead.name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.phone}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.email || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${getScoreBadge(lead.lead_score)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.budget_indication || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${lead.timeline || '-'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <button onclick="viewLeadDetails('${lead.id}')" class="text-blue-600 hover:text-blue-800">
                        <i class="fas fa-eye"></i> View
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error filtering leads:', error);
    }
}

/**
 * Refresh appointments calendar
 */
async function refreshAppointments() {
    try {
        const response = await fetch(`${API_BASE}/api/appointments`);
        if (!response.ok) throw new Error('Failed to fetch appointments');
        
        const data = await response.json();
        const container = document.getElementById('appointments-calendar');
        
        if (!container) return;
        
        if (data.appointments.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8 col-span-3">No appointments scheduled</p>';
            return;
        }
        
        container.innerHTML = data.appointments.map(appt => `
            <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between mb-2">
                    <h4 class="font-semibold text-gray-900">${appt.customer_name}</h4>
                    ${getAppointmentStatusBadge(appt.status)}
                </div>
                <div class="space-y-1 text-sm text-gray-600">
                    <p><i class="fas fa-calendar mr-2"></i>${formatDateTime(appt.appointment_datetime)}</p>
                    <p><i class="fas fa-clock mr-2"></i>${appt.duration_minutes} minutes</p>
                    <p><i class="fas fa-briefcase mr-2"></i>${appt.service_type}</p>
                    <p><i class="fas fa-phone mr-2"></i>${appt.customer_phone}</p>
                </div>
                ${appt.notes ? `<p class="mt-2 text-xs text-gray-500 italic">${appt.notes}</p>` : ''}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error refreshing appointments:', error);
    }
}

/**
 * Setup form submission handlers
 */
function setupFormHandlers() {
    // Load current configuration
    loadCurrentConfiguration();
    
    // Business hours form
    const businessHoursForm = document.getElementById('business-hours-form');
    if (businessHoursForm) {
        businessHoursForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveConfiguration('business_hours', {
                weekday_start: e.target[0].value,
                weekday_end: e.target[1].value
            });
        });
    }
    
    // Greeting form
    const greetingForm = document.getElementById('greeting-form');
    if (greetingForm) {
        greetingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveConfiguration('greeting', {
                message: e.target[0].value
            });
        });
    }
    
    // Company description form
    const companyDescriptionForm = document.getElementById('company-description-form');
    if (companyDescriptionForm) {
        companyDescriptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const descriptionText = document.getElementById('company-description-text').value.trim();
            if (!descriptionText) {
                alert('Company description cannot be empty');
                return;
            }
            await saveConfiguration('company_description', {
                text: descriptionText
            });
        });
    }
    
    // Word count for company description
    const descriptionTextarea = document.getElementById('company-description-text');
    if (descriptionTextarea) {
        descriptionTextarea.addEventListener('input', updateWordCount);
    }
    
    // Personality form
    const personalityForm = document.getElementById('personality-form');
    if (personalityForm) {
        personalityForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveConfiguration('personality', {
                tone: e.target[0].value,
                style: e.target[1].value
            });
        });
    }
}

/**
 * Update word count for company description
 */
function updateWordCount() {
    const textarea = document.getElementById('company-description-text');
    const wordCountSpan = document.getElementById('description-word-count');
    if (textarea && wordCountSpan) {
        const text = textarea.value.trim();
        const wordCount = text ? text.split(/\s+/).length : 0;
        wordCountSpan.textContent = `${wordCount} words`;
        
        // Color code based on recommended range
        if (wordCount === 0) {
            wordCountSpan.className = 'text-gray-500';
        } else if (wordCount < 50) {
            wordCountSpan.className = 'text-yellow-600';
        } else if (wordCount <= 200) {
            wordCountSpan.className = 'text-green-600';
        } else {
            wordCountSpan.className = 'text-orange-600';
        }
    }
}

/**
 * Load current configuration from backend
 */
async function loadCurrentConfiguration() {
    try {
        console.log('Loading configuration...');
        const response = await fetch(`${API_BASE}/api/config`);
        if (!response.ok) throw new Error('Failed to fetch configuration');
        
        const data = await response.json();
        console.log('Configuration data:', data);
        
        if (data.success && data.config) {
            const config = data.config;
            
            // Load greeting
            const greetingTextarea = document.querySelector('#greeting-form textarea');
            if (greetingTextarea && config.greeting && config.greeting.message) {
                greetingTextarea.value = config.greeting.message;
                console.log('✅ Greeting loaded:', config.greeting.message.substring(0, 50) + '...');
            }
            
            // Load business hours
            if (config.business_hours) {
                const timeInputs = document.querySelectorAll('#business-hours-form input[type="time"]');
                if (timeInputs.length >= 2) {
                    if (config.business_hours.weekday_start) {
                        timeInputs[0].value = config.business_hours.weekday_start;
                    }
                    if (config.business_hours.weekday_end) {
                        timeInputs[1].value = config.business_hours.weekday_end;
                    }
                    console.log('✅ Business hours loaded:', config.business_hours);
                }
            }
            
            // Load personality
            if (config.personality) {
                const selects = document.querySelectorAll('#personality-form select');
                if (selects.length >= 2) {
                    // Tone select
                    if (config.personality.tone) {
                        const toneValue = config.personality.tone.charAt(0).toUpperCase() + config.personality.tone.slice(1);
                        selects[0].value = toneValue;
                    }
                    // Style select
                    if (config.personality.style) {
                        const styleValue = config.personality.style.charAt(0).toUpperCase() + config.personality.style.slice(1);
                        selects[1].value = styleValue;
                    }
                    console.log('✅ Personality loaded:', config.personality);
                }
            }
            
            // Load company description
            const descriptionTextarea = document.getElementById('company-description-text');
            if (descriptionTextarea && config.company_description && config.company_description.text) {
                descriptionTextarea.value = config.company_description.text;
                updateWordCount();
                console.log('✅ Company description loaded:', config.company_description.text.substring(0, 50) + '...');
            }
            
            console.log('✅ Configuration loaded successfully');
        }
        
    } catch (error) {
        console.error('Error loading configuration:', error);
    }
}

/**
 * Save configuration to backend
 */
async function saveConfiguration(type, data) {
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: type,
                data: data
            })
        });
        
        if (!response.ok) throw new Error('Failed to save configuration');
        
        const result = await response.json();
        alert(`Configuration saved successfully!`);
        
    } catch (error) {
        console.error('Error saving configuration:', error);
        alert('Failed to save configuration. Please try again.');
    }
}

/**
 * Handle file upload for documents
 */
async function handleFileUpload(event) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    
    try {
        // Show uploading message
        const container = document.getElementById('documents-list');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-spinner fa-spin text-4xl mb-2"></i>
                    <p>Uploading documents...</p>
                </div>
            `;
        }
        
        const response = await fetch(`${API_BASE}/api/documents`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Failed to upload documents');
        
        const result = await response.json();
        
        if (result.success) {
            alert(`✅ ${result.uploaded} document(s) uploaded successfully!\n\n${result.message || 'AI will use this information in conversations.'}`);
        } else {
            alert(`❌ Upload failed: ${result.error || 'Unknown error'}`);
        }
        
        // Clear file input
        event.target.value = '';
        
        // Refresh documents list
        await refreshDocumentsList();
        
    } catch (error) {
        console.error('Error uploading documents:', error);
        alert('Failed to upload documents. Please try again.');
        
        // Refresh documents list anyway
        await refreshDocumentsList();
    }
}

/**
 * Refresh documents list
 */
async function refreshDocumentsList() {
    const container = document.getElementById('documents-list');
    if (!container) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/documents`);
        if (!response.ok) throw new Error('Failed to fetch documents');
        
        const data = await response.json();
        
        if (data.success && data.documents && data.documents.length > 0) {
            container.innerHTML = data.documents.map(doc => {
                const uploadedDate = new Date(doc.uploaded_at);
                const timeAgo = getTimeAgo(uploadedDate);
                const fileIcon = getFileIcon(doc.file_type);
                const fileSize = formatFileSize(doc.size);
                
                return `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div class="flex items-center space-x-3">
                            <i class="fas ${fileIcon} text-xl"></i>
                            <div>
                                <p class="text-sm font-medium text-gray-900">${doc.filename}</p>
                                <p class="text-xs text-gray-500">${fileSize} • Uploaded ${timeAgo}</p>
                            </div>
                        </div>
                        <button onclick="deleteDocument('${doc.id}')" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-file-upload text-4xl mb-2"></i>
                    <p>No documents uploaded yet</p>
                    <p class="text-sm">Upload your first document to get started</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading documents:', error);
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <p>Unable to load documents</p>
            </div>
        `;
    }
}

/**
 * Get file icon based on file type
 */
function getFileIcon(fileType) {
    if (fileType && fileType.includes('pdf')) return 'fa-file-pdf text-red-500';
    if (fileType && fileType.includes('word')) return 'fa-file-word text-blue-500';
    if (fileType && fileType.includes('text')) return 'fa-file-alt text-gray-500';
    return 'fa-file text-gray-500';
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get time ago string
 */
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    
    return date.toLocaleDateString();
}

/**
 * Delete document (placeholder)
 */
function deleteDocument(docId) {
    if (confirm('Are you sure you want to delete this document?')) {
        alert(`Delete document ${docId}\n(Feature coming soon)`);
        // TODO: Implement DELETE /api/documents/:id endpoint
    }
}

/**
 * Utility functions for formatting
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDuration(seconds) {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
}

function formatIntent(intent) {
    if (!intent) return 'Unknown';
    return intent.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getStatusBadge(status) {
    const badges = {
        'completed': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Completed</span>',
        'in_progress': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">In Progress</span>',
        'failed': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Failed</span>',
        'initiated': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Initiated</span>'
    };
    return badges[status] || '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Unknown</span>';
}

function getScoreBadge(score) {
    if (!score) return '-';
    
    let colorClass = 'bg-gray-100 text-gray-800';
    if (score >= 7) colorClass = 'bg-green-100 text-green-800';
    else if (score >= 4) colorClass = 'bg-yellow-100 text-yellow-800';
    else colorClass = 'bg-red-100 text-red-800';
    
    return `<span class="px-2 py-1 text-xs font-semibold rounded-full ${colorClass}">${score}/10</span>`;
}

function getAppointmentStatusBadge(status) {
    const badges = {
        'scheduled': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Scheduled</span>',
        'completed': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Completed</span>',
        'cancelled': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Cancelled</span>'
    };
    return badges[status] || '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Unknown</span>';
}

/**
 * View call details (with conversation and insights)
 */
async function viewCallDetails(callId) {
    try {
        const response = await fetch(`${API_BASE}/api/calls/${callId}`);
        if (!response.ok) throw new Error('Failed to fetch call details');
        
        const data = await response.json();
        
        if (data.success) {
            showCallDetailsModal(data.call, data.conversation, data.insights);
        } else {
            alert('Failed to load call details: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error loading call details:', error);
        alert('Failed to load call details. Please try again.');
    }
}

/**
 * Show call details in a modal
 */
function showCallDetailsModal(call, conversation, insights) {
    // Create modal HTML
    const modalHTML = `
        <div id="call-details-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onclick="closeCallDetailsModal(event)">
            <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" onclick="event.stopPropagation()">
                <!-- Header -->
                <div class="bg-blue-600 text-white px-6 py-4 flex justify-between items-center">
                    <h2 class="text-xl font-bold">Call Details</h2>
                    <button onclick="closeCallDetailsModal()" class="text-white hover:text-gray-200">
                        <i class="fas fa-times text-2xl"></i>
                    </button>
                </div>
                
                <!-- Content -->
                <div class="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
                    <!-- Call Info -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div>
                            <p class="text-sm text-gray-600">Caller</p>
                            <p class="font-semibold">${call.caller_phone}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Duration</p>
                            <p class="font-semibold">${formatDuration(call.duration_seconds)}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Intent</p>
                            <p class="font-semibold">${formatIntent(call.intent)}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Language</p>
                            <p class="font-semibold">${getLanguageName(call.language)}</p>
                        </div>
                    </div>
                    
                    <!-- Insights -->
                    <div class="bg-blue-50 rounded-lg p-4 mb-6">
                        <h3 class="font-bold text-lg mb-3 flex items-center">
                            <i class="fas fa-lightbulb text-yellow-500 mr-2"></i>
                            AI Insights
                        </h3>
                        
                        <!-- Summary -->
                        <div class="mb-4">
                            <p class="text-sm font-semibold text-gray-700 mb-1">Summary</p>
                            <p class="text-sm text-gray-600">${insights.summary || 'No summary available'}</p>
                        </div>
                        
                        <!-- Key Points -->
                        ${insights.key_points && insights.key_points.length > 0 ? `
                            <div class="mb-4">
                                <p class="text-sm font-semibold text-gray-700 mb-1">Key Points</p>
                                <ul class="list-disc list-inside text-sm text-gray-600">
                                    ${insights.key_points.map(point => `<li>${point}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        
                        <!-- Topics & Sentiment -->
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            ${insights.topics && insights.topics.length > 0 ? `
                                <div>
                                    <p class="text-sm font-semibold text-gray-700 mb-1">Topics</p>
                                    <div class="flex flex-wrap gap-2">
                                        ${insights.topics.map(topic => `
                                            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${topic}</span>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : `
                                <div>
                                    <p class="text-sm font-semibold text-gray-700 mb-1">Topics</p>
                                    <p class="text-xs text-gray-500">Will be available after call completes</p>
                                </div>
                            `}
                            
                            <div>
                                <p class="text-sm font-semibold text-gray-700 mb-1">Sentiment</p>
                                ${insights.sentiment && insights.sentiment !== 'neutral' ? `
                                    <span class="px-2 py-1 ${getSentimentColor(insights.sentiment)} text-xs rounded">
                                        ${insights.sentiment.toUpperCase()}
                                    </span>
                                ` : `
                                    <p class="text-xs text-gray-500">Will be analyzed after call completes</p>
                                `}
                            </div>
                        </div>
                        
                        <!-- Customer Satisfaction -->
                        ${insights.customer_satisfaction && insights.customer_satisfaction !== 'unknown' ? `
                            <div class="mb-4">
                                <p class="text-sm font-semibold text-gray-700 mb-1">Customer Satisfaction</p>
                                <span class="px-2 py-1 ${getSatisfactionColor(insights.customer_satisfaction)} text-xs rounded">
                                    ${insights.customer_satisfaction.toUpperCase()}
                                </span>
                            </div>
                        ` : ''}
                        
                        <!-- Action Items -->
                        ${insights.action_items && insights.action_items.length > 0 ? `
                            <div>
                                <p class="text-sm font-semibold text-gray-700 mb-1">Action Items</p>
                                <ul class="list-disc list-inside text-sm text-gray-600">
                                    ${insights.action_items.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Conversation Log -->
                    <div class="bg-gray-50 rounded-lg p-4">
                        <h3 class="font-bold text-lg mb-3 flex items-center">
                            <i class="fas fa-comments text-blue-500 mr-2"></i>
                            Conversation Log
                        </h3>
                        
                        ${conversation && conversation.length > 0 ? `
                            <div class="space-y-3">
                                ${conversation.map(turn => `
                                    <div class="flex ${turn.speaker === 'caller' ? 'justify-start' : 'justify-end'}">
                                        <div class="max-w-[80%] ${turn.speaker === 'caller' ? 'bg-white' : 'bg-blue-100'} rounded-lg p-3 shadow-sm">
                                            <p class="text-xs font-semibold ${turn.speaker === 'caller' ? 'text-gray-700' : 'text-blue-700'} mb-1">
                                                ${turn.speaker === 'caller' ? '👤 Customer' : '🤖 AI Assistant'}
                                            </p>
                                            <p class="text-sm text-gray-800">${turn.text}</p>
                                            ${turn.timestamp_ms ? `
                                                <p class="text-xs text-gray-500 mt-1">${formatTimestamp(turn.timestamp_ms)}</p>
                                            ` : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<p class="text-gray-500 text-center py-4">No conversation data available</p>'}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

/**
 * Close call details modal
 */
function closeCallDetailsModal(event) {
    // Close if clicking outside modal or on close button
    if (!event || event.target.id === 'call-details-modal' || event.type === 'click') {
        const modal = document.getElementById('call-details-modal');
        if (modal) {
            modal.remove();
        }
    }
}

/**
 * Get language name from code
 */
function getLanguageName(code) {
    const languages = {
        'en': 'English',
        'hi': 'Hindi',
        'ta': 'Tamil',
        'te': 'Telugu',
        'bn': 'Bengali'
    };
    return languages[code] || code || 'Unknown';
}

/**
 * Get sentiment color class
 */
function getSentimentColor(sentiment) {
    const colors = {
        'positive': 'bg-green-100 text-green-800',
        'negative': 'bg-red-100 text-red-800',
        'neutral': 'bg-gray-100 text-gray-800'
    };
    return colors[sentiment] || 'bg-gray-100 text-gray-800';
}

/**
 * Get customer satisfaction color class
 */
function getSatisfactionColor(satisfaction) {
    const colors = {
        'satisfied': 'bg-green-100 text-green-800',
        'unsatisfied': 'bg-red-100 text-red-800',
        'neutral': 'bg-gray-100 text-gray-800',
        'unknown': 'bg-gray-100 text-gray-800'
    };
    return colors[satisfaction] || 'bg-gray-100 text-gray-800';
}

/**
 * Format timestamp from milliseconds
 */
function formatTimestamp(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * View lead details (placeholder)
 */
function viewLeadDetails(leadId) {
    alert(`View lead details: ${leadId}\n(Feature coming soon)`);
}
