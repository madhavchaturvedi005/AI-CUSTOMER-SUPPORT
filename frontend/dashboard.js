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
        button.classList.remove('active', 'bg-gradient-to-br', 'from-blue-500', 'to-blue-600', 'text-white', 'shadow-md');
        button.classList.add('text-gray-600', 'hover:bg-gray-50');
    });
    
    // Show selected tab content
    const selectedContent = document.getElementById(`content-${tabName}`);
    if (selectedContent) {
        selectedContent.classList.remove('hidden');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.getElementById(`tab-${tabName}`);
    if (selectedButton) {
        selectedButton.classList.remove('text-gray-600', 'hover:bg-gray-50');
        selectedButton.classList.add('active', 'bg-gradient-to-br', 'from-blue-500', 'to-blue-600', 'text-white', 'shadow-md');
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
        document.getElementById('stat-duration').textContent = data.avg_duration ? `${data.avg_duration}m` : '3m';
        
        // Update call volume chart with mock data if no real data
        if (callVolumeChart) {
            if (data.call_volume && data.call_volume.labels && data.call_volume.labels.length > 0) {
                callVolumeChart.data.labels = data.call_volume.labels;
                callVolumeChart.data.datasets[0].data = data.call_volume.data;
            } else {
                // Mock data for call volume (last 7 days)
                callVolumeChart.data.labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                callVolumeChart.data.datasets[0].data = [12, 19, 15, 22, 18, 25, 20];
            }
            callVolumeChart.update();
        }
        
        // Update intent distribution chart with mock data emphasizing support and appointments
        if (intentChart) {
            if (data.intent_distribution && data.intent_distribution.labels && data.intent_distribution.labels.length > 0) {
                intentChart.data.labels = data.intent_distribution.labels;
                intentChart.data.datasets[0].data = data.intent_distribution.data;
            } else {
                // Mock data with Support and Appointment Booking as highest
                intentChart.data.labels = ['Support', 'Appointment Booking', 'Sales Inquiry', 'General Info', 'Complaint', 'Other'];
                intentChart.data.datasets[0].data = [35, 30, 15, 10, 7, 3];
            }
            intentChart.update();
        }
        
        // Update recent activity
        updateRecentActivity(data.recent_activity || []);
        
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        
        // Load mock data on error
        if (callVolumeChart) {
            callVolumeChart.data.labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            callVolumeChart.data.datasets[0].data = [12, 19, 15, 22, 18, 25, 20];
            callVolumeChart.update();
        }
        
        if (intentChart) {
            intentChart.data.labels = ['Support', 'Appointment Booking', 'Sales Inquiry', 'General Info', 'Complaint', 'Other'];
            intentChart.data.datasets[0].data = [35, 30, 15, 10, 7, 3];
            intentChart.update();
        }
    }
}

/**
 * Update recent activity feed
 */
function updateRecentActivity(activities) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    // If no activities provided, use mock data
    if (activities.length === 0) {
        activities = [
            { type: 'appointment', title: 'New appointment booked', time: '5 minutes ago' },
            { type: 'call', title: 'Incoming call completed', time: '12 minutes ago' },
            { type: 'lead', title: 'High-value lead captured', time: '23 minutes ago' },
            { type: 'appointment', title: 'Appointment confirmed', time: '45 minutes ago' },
            { type: 'call', title: 'Support call resolved', time: '1 hour ago' }
        ];
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
                    <button onclick="viewCallDetails('${call.id}')" class="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium text-xs">
                        <i class="fas fa-eye mr-1.5"></i> View Details
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
                    <button onclick="viewLeadDetails('${lead.id}')" class="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium text-xs">
                        <i class="fas fa-eye mr-1.5"></i> View Details
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
                    <button onclick="viewLeadDetails('${lead.id}')" class="inline-flex items-center px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-medium text-xs">
                        <i class="fas fa-eye mr-1.5"></i> View Details
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
            <div class="appointment-card bg-white border-2 border-gray-100 rounded-2xl p-5 hover:shadow-lg transition-all">
                <div class="flex items-start justify-between mb-3">
                    <h4 class="font-bold text-gray-900 text-lg">${appt.customer_name}</h4>
                    ${getAppointmentStatusBadge(appt.status)}
                </div>
                <div class="space-y-2.5 text-sm text-gray-600">
                    <p class="flex items-center">
                        <i class="fas fa-calendar w-5 text-blue-500"></i>
                        <span class="font-medium">${formatDateTime(appt.appointment_datetime)}</span>
                    </p>
                    <p class="flex items-center">
                        <i class="fas fa-clock w-5 text-purple-500"></i>
                        <span>${appt.duration_minutes} minutes</span>
                    </p>
                    <p class="flex items-center">
                        <i class="fas fa-briefcase w-5 text-green-500"></i>
                        <span>${appt.service_type}</span>
                    </p>
                    <p class="flex items-center">
                        <i class="fas fa-phone w-5 text-orange-500"></i>
                        <span>${appt.customer_phone}</span>
                    </p>
                </div>
                ${appt.notes ? `<p class="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500 italic">${appt.notes}</p>` : ''}
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
    
    // Business name form
    const businessNameForm = document.getElementById('business-name-form');
    if (businessNameForm) {
        businessNameForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const businessName = document.getElementById('business-name-input').value.trim();
            if (!businessName) {
                alert('Business name cannot be empty');
                return;
            }
            await saveConfiguration('business_name', {
                name: businessName
            });
        });
    }
    
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
            
            // Load business name
            const businessNameInput = document.getElementById('business-name-input');
            if (businessNameInput && config.business_name && config.business_name.name) {
                businessNameInput.value = config.business_name.name;
                console.log('✅ Business name loaded:', config.business_name.name);
            }
            
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
            // Add summary header
            const summaryHtml = `
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-5 mb-6 border border-blue-200">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <div class="bg-blue-500 p-3 rounded-lg">
                                <i class="fas fa-database text-white text-2xl"></i>
                            </div>
                            <div>
                                <h4 class="text-lg font-bold text-gray-900">Qdrant Vector Database</h4>
                                <p class="text-sm text-gray-600 mt-1">
                                    <span class="font-semibold text-blue-600">${data.documents.length}</span> document${data.documents.length !== 1 ? 's' : ''} indexed
                                    ${data.total_chunks ? `<span class="mx-2">•</span><span class="font-semibold text-indigo-600">${data.total_chunks}</span> vector chunks` : ''}
                                </p>
                            </div>
                        </div>
                        <button onclick="refreshDocumentsList()" class="bg-white hover:bg-gray-50 text-gray-700 px-4 py-2 rounded-lg border border-gray-200 transition-all font-medium text-sm">
                            <i class="fas fa-sync-alt mr-2"></i>Refresh
                        </button>
                    </div>
                </div>
            `;
            
            const documentsHtml = data.documents.map(doc => {
                const uploadedDate = doc.uploaded_at ? new Date(doc.uploaded_at) : null;
                const timeAgo = uploadedDate ? getTimeAgo(uploadedDate) : 'Unknown';
                const fileIcon = getFileIcon(doc.file_type);
                const fileSize = formatFileSize(doc.size);
                
                return `
                    <div class="bg-white rounded-xl border border-gray-200 hover:shadow-lg transition-all overflow-hidden">
                        <div class="flex items-center justify-between p-5">
                            <div class="flex items-center space-x-4 flex-1">
                                <div class="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-xl shadow-sm">
                                    <i class="fas ${fileIcon} text-3xl"></i>
                                </div>
                                <div class="flex-1">
                                    <div class="flex items-center space-x-3 mb-2">
                                        <p class="text-base font-bold text-gray-900">${doc.filename}</p>
                                        ${doc.chunk_count ? `<span class="bg-blue-100 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded-full">${doc.chunk_count} chunks</span>` : ''}
                                    </div>
                                    <div class="flex items-center space-x-4 text-xs text-gray-500">
                                        <span class="flex items-center">
                                            <i class="fas fa-hdd mr-1.5 text-gray-400"></i>
                                            <span class="font-medium">${fileSize}</span>
                                        </span>
                                        <span class="flex items-center">
                                            <i class="fas fa-clock mr-1.5 text-gray-400"></i>
                                            <span>Uploaded ${timeAgo}</span>
                                        </span>
                                        ${doc.file_type ? `
                                        <span class="flex items-center">
                                            <i class="fas fa-tag mr-1.5 text-gray-400"></i>
                                            <span class="uppercase">${doc.file_type.split('/').pop()}</span>
                                        </span>
                                        ` : ''}
                                    </div>
                                    ${doc.vector_count ? `
                                    <div class="mt-2 flex items-center space-x-2">
                                        <span class="text-xs text-gray-500">
                                            <i class="fas fa-vector-square mr-1 text-indigo-500"></i>
                                            ${doc.vector_count} vectors in Qdrant
                                        </span>
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <button onclick="viewDocumentDetails('${doc.id}')" 
                                    class="bg-blue-50 hover:bg-blue-100 text-blue-600 px-4 py-2 rounded-lg transition-all font-medium text-sm">
                                    <i class="fas fa-eye mr-1.5"></i>View
                                </button>
                                <button onclick="deleteDocument('${doc.id}')" 
                                    class="bg-red-50 hover:bg-red-100 text-red-600 px-4 py-2 rounded-lg transition-all font-medium text-sm">
                                    <i class="fas fa-trash mr-1.5"></i>Delete
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = summaryHtml + documentsHtml;
        } else {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <div class="bg-gray-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-file-upload text-4xl text-gray-400"></i>
                    </div>
                    <p class="text-lg font-semibold text-gray-700 mb-2">No documents uploaded yet</p>
                    <p class="text-sm text-gray-500">Upload your first document to build your AI knowledge base</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading documents:', error);
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <div class="bg-red-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-400"></i>
                </div>
                <p class="text-lg font-semibold text-gray-700 mb-2">Unable to load documents</p>
                <p class="text-sm text-gray-500">${error.message}</p>
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
 * View document details
 */
async function viewDocumentDetails(docId) {
    try {
        const response = await fetch(`${API_BASE}/api/documents/${docId}`);
        if (!response.ok) throw new Error('Failed to fetch document details');
        
        const data = await response.json();
        
        if (data.success && data.document) {
            const doc = data.document;
            const chunks = data.chunks || [];
            
            let detailsHtml = `
                <div class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                    <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                        <div class="bg-gradient-to-r from-blue-500 to-indigo-600 p-6 text-white">
                            <div class="flex items-center justify-between">
                                <div>
                                    <h3 class="text-2xl font-bold mb-2">${doc.filename}</h3>
                                    <p class="text-blue-100 text-sm">Document Details & Vector Information</p>
                                </div>
                                <button onclick="closeDocumentDetails()" class="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-lg transition-all">
                                    <i class="fas fa-times text-2xl"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                            <!-- Document Info -->
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                <div class="bg-gray-50 p-4 rounded-xl">
                                    <p class="text-xs text-gray-500 mb-1">File Size</p>
                                    <p class="text-lg font-bold text-gray-900">${formatFileSize(doc.size)}</p>
                                </div>
                                <div class="bg-blue-50 p-4 rounded-xl">
                                    <p class="text-xs text-blue-600 mb-1">Chunks</p>
                                    <p class="text-lg font-bold text-blue-700">${doc.chunk_count || 0}</p>
                                </div>
                                <div class="bg-indigo-50 p-4 rounded-xl">
                                    <p class="text-xs text-indigo-600 mb-1">Vectors</p>
                                    <p class="text-lg font-bold text-indigo-700">${doc.vector_count || 0}</p>
                                </div>
                                <div class="bg-green-50 p-4 rounded-xl">
                                    <p class="text-xs text-green-600 mb-1">Status</p>
                                    <p class="text-lg font-bold text-green-700">Active</p>
                                </div>
                            </div>
                            
                            <!-- Metadata -->
                            <div class="bg-gray-50 rounded-xl p-5 mb-6">
                                <h4 class="font-bold text-gray-900 mb-3 flex items-center">
                                    <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                                    Metadata
                                </h4>
                                <div class="grid grid-cols-2 gap-3 text-sm">
                                    <div>
                                        <span class="text-gray-500">File Type:</span>
                                        <span class="ml-2 font-medium text-gray-900">${doc.file_type || 'Unknown'}</span>
                                    </div>
                                    <div>
                                        <span class="text-gray-500">Uploaded:</span>
                                        <span class="ml-2 font-medium text-gray-900">${doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : 'Unknown'}</span>
                                    </div>
                                    <div>
                                        <span class="text-gray-500">Document ID:</span>
                                        <span class="ml-2 font-mono text-xs text-gray-700">${doc.id}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Chunks Preview -->
                            ${chunks.length > 0 ? `
                            <div class="bg-white rounded-xl border border-gray-200 p-5">
                                <h4 class="font-bold text-gray-900 mb-4 flex items-center">
                                    <i class="fas fa-th-list text-indigo-500 mr-2"></i>
                                    Text Chunks (${chunks.length})
                                </h4>
                                <div class="space-y-3 max-h-96 overflow-y-auto">
                                    ${chunks.map((chunk, idx) => `
                                        <div class="bg-gradient-to-r from-gray-50 to-white p-4 rounded-lg border border-gray-200">
                                            <div class="flex items-center justify-between mb-2">
                                                <span class="text-xs font-bold text-gray-500">Chunk ${idx + 1}</span>
                                                <span class="text-xs text-gray-400">${chunk.text ? chunk.text.length : 0} characters</span>
                                            </div>
                                            <p class="text-sm text-gray-700 leading-relaxed">${chunk.text ? chunk.text.substring(0, 200) + (chunk.text.length > 200 ? '...' : '') : 'No text'}</p>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            ` : `
                            <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-5 text-center">
                                <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mb-2"></i>
                                <p class="text-sm text-yellow-700">No chunks available for this document</p>
                            </div>
                            `}
                        </div>
                    </div>
                </div>
            `;
            
            // Add to body
            const modal = document.createElement('div');
            modal.id = 'document-details-modal';
            modal.innerHTML = detailsHtml;
            document.body.appendChild(modal);
        } else {
            alert('Failed to load document details');
        }
    } catch (error) {
        console.error('Error viewing document details:', error);
        alert('Failed to load document details: ' + error.message);
    }
}

/**
 * Close document details modal
 */
function closeDocumentDetails() {
    const modal = document.getElementById('document-details-modal');
    if (modal) {
        modal.remove();
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

// Make function globally accessible
window.viewCallDetails = viewCallDetails;

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

// Make function globally accessible
window.closeCallDetailsModal = closeCallDetailsModal;

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

// Make function globally accessible
window.viewLeadDetails = viewLeadDetails;

/**
 * Open booking modal
 */
function openBookingModal() {
    const modal = document.getElementById('bookingModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Set default datetime to tomorrow at 10 AM
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(10, 0, 0, 0);
        const datetimeInput = document.getElementById('bDateTime');
        if (datetimeInput) {
            datetimeInput.value = tomorrow.toISOString().slice(0, 16);
        }
    }
}

// Make function globally accessible
window.openBookingModal = openBookingModal;

/**
 * Close booking modal
 */
function closeBookingModal() {
    const modal = document.getElementById('bookingModal');
    if (modal) {
        modal.classList.add('hidden');
        // Reset form
        const form = document.getElementById('booking-form');
        if (form) {
            form.reset();
        }
    }
}

// Make function globally accessible
window.closeBookingModal = closeBookingModal;

/**
 * Submit booking form
 */
async function submitBooking() {
    try {
        // Get form values
        const customerName = document.getElementById('bName').value.trim();
        const customerPhone = document.getElementById('bPhone').value.trim();
        const serviceType = document.getElementById('bService').value.trim();
        const appointmentDatetime = document.getElementById('bDateTime').value;
        const notes = document.getElementById('bNotes').value.trim();
        
        // Validate required fields
        if (!customerName || !customerPhone || !serviceType || !appointmentDatetime) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Convert datetime-local to ISO string
        const appointmentDate = new Date(appointmentDatetime);
        const isoDatetime = appointmentDate.toISOString();
        
        // Prepare request body
        const requestBody = {
            customer_name: customerName,
            customer_phone: customerPhone,
            service_type: serviceType,
            appointment_datetime: isoDatetime,
            duration_minutes: 30,
            notes: notes || null,
            call_id: null
        };
        
        // Send POST request
        const response = await fetch(`${API_BASE}/api/appointments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'Appointment booked successfully!');
            closeBookingModal();
            refreshAppointments();
        } else {
            alert('Error: ' + (data.error || 'Failed to book appointment'));
        }
        
    } catch (error) {
        console.error('Error submitting booking:', error);
        alert('Network error: Failed to book appointment. Please try again.');
    }
}

// Add form submit handler for booking form
document.addEventListener('DOMContentLoaded', () => {
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', (e) => {
            e.preventDefault();
            submitBooking();
        });
    }
});

// Auto-refresh appointments every 15 seconds
setInterval(() => {
    const appointmentsTab = document.getElementById('content-appointments');
    if (appointmentsTab && !appointmentsTab.classList.contains('hidden')) {
        refreshAppointments();
    }
}, 15000);
