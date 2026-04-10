/**
 * Real-time event handling for dashboard via Server-Sent Events (SSE)
 */

(function startLiveFeed() {
    const es = new EventSource('/api/events/live');
    
    es.onmessage = function(e) {
        try {
            const event = JSON.parse(e.data);
            handleLiveEvent(event);
        } catch (err) {
            console.warn('SSE parse error:', err);
        }
    };
    
    es.onerror = function() {
        // Browser auto-reconnects SSE — no manual retry needed
        console.log('SSE reconnecting...');
    };
    
    function handleLiveEvent(event) {
        switch (event.type) {
            case 'transcript':
                // Append a new row to the live transcript panel
                appendTranscriptRow({
                    speaker: event.speaker,
                    text: event.text,
                    language: event.language,
                    timestamp_ms: event.timestamp_ms,
                    call_sid: event.call_sid
                });
                break;
            
            case 'call_start':
                // Show a new active call banner / update active calls count
                showActiveCallBanner(event.call_sid, event.caller_phone);
                break;
            
            case 'call_update':
                // Update intent badge, language pill, lead score
                updateCallMetadata(event.call_sid, {
                    intent: event.intent,
                    language: event.language,
                    lead_score: event.lead_score,
                    intent_confidence: event.intent_confidence,
                    language_confidence: event.language_confidence
                });
                break;
            
            case 'call_end':
                // Remove active call banner, refresh call history table
                removeActiveCallBanner(event.call_sid);
                refreshCallHistory();
                break;
            
            case 'tool_execution':
                // Handle tool execution events (appointments, leads, etc.)
                handleToolExecution(event);
                break;
            
            case 'appointment_booked':
                // Refresh appointments table and dashboard
                refreshAppointments();
                refreshDashboard();
                break;
            
            case 'lead_created':
                // Refresh leads table and dashboard
                refreshLeads();
                refreshDashboard();
                break;
            
            case 'complaint_logged':
                // Show complaint notification
                showNotification('warning', `Complaint logged from ${event.caller_phone}`);
                refreshDashboard();
                break;
        }
    }
    
    // DOM manipulation functions
    
    function appendTranscriptRow({ speaker, text, language, timestamp_ms, call_sid }) {
        // Find or create transcript container for this call_sid
        const container = document.getElementById('live-transcript')
            || document.querySelector('[data-call-sid="' + call_sid + '"] .transcript');
        
        if (!container) return;
        
        const row = document.createElement('div');
        row.className = 'transcript-row transcript-' + speaker;
        row.innerHTML = `
            <span class="speaker-label">${speaker === 'customer' || speaker === 'caller' ? 'Caller' : 'AI'}</span>
            <span class="transcript-text">${escapeHtml(text)}</span>
            <span class="transcript-lang">${language}</span>
        `;
        
        container.appendChild(row);
        container.scrollTop = container.scrollHeight;
    }
    
    function showActiveCallBanner(call_sid, caller_phone) {
        const banner = document.getElementById('active-call-banner');
        if (banner) {
            banner.textContent = 'Live call: ' + (caller_phone || call_sid);
            banner.style.display = 'block';
            banner.dataset.callSid = call_sid;
        }
    }
    
    function updateCallMetadata(call_sid, { intent, language, lead_score, intent_confidence, language_confidence }) {
        const intentEl = document.getElementById('live-intent');
        const langEl = document.getElementById('live-language');
        const scoreEl = document.getElementById('live-lead-score');
        
        if (intent && intentEl) {
            intentEl.textContent = intent.replace(/_/g, ' ');
            if (intent_confidence) {
                intentEl.title = `Confidence: ${(intent_confidence * 100).toFixed(0)}%`;
            }
        }
        
        if (language && langEl) {
            langEl.textContent = language.toUpperCase();
            if (language_confidence) {
                langEl.title = `Confidence: ${(language_confidence * 100).toFixed(0)}%`;
            }
        }
        
        if (lead_score !== undefined && scoreEl) {
            scoreEl.textContent = lead_score;
        }
    }
    
    function removeActiveCallBanner(call_sid) {
        const banner = document.getElementById('active-call-banner');
        if (banner && banner.dataset.callSid === call_sid) {
            banner.style.display = 'none';
        }
    }
    
    function refreshCallHistory() {
        // Re-fetch the calls list and re-render the table
        fetch('/api/calls')
            .then(r => r.json())
            .then(data => {
                if (window.renderCallsTable) {
                    window.renderCallsTable(data.calls);
                }
            })
            .catch(err => console.error('Error refreshing calls:', err));
    }
    
    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    function handleToolExecution(event) {
        const { tool_name, success, result } = event;
        
        if (!success) {
            console.warn('Tool execution failed:', tool_name, result);
            return;
        }
        
        // Handle specific tool types
        switch (tool_name) {
            case 'book_appointment':
                if (result && result.appointment_id) {
                    // Refresh appointments table and dashboard
                    refreshAppointments();
                    refreshDashboard();
                }
                break;
            
            case 'create_lead':
                if (result && result.lead_id) {
                    // Refresh leads table and dashboard
                    refreshLeads();
                    refreshDashboard();
                }
                break;
            
            case 'check_availability':
                // Show availability check in activity feed
                if (result && result.message) {
                    addActivityItem('availability', result.message);
                }
                break;
            
            case 'get_available_slots':
                // Show available slots in activity feed
                if (result && result.available_slots) {
                    addActivityItem('slots', 
                        `Available times: ${result.available_slots.slice(0, 3).join(', ')}...`
                    );
                }
                break;
        }
    }
    
    function refreshAppointments() {
        // Fetch and update appointments table
        fetch('/api/appointments')
            .then(r => r.json())
            .then(data => {
                if (window.renderAppointmentsTable) {
                    window.renderAppointmentsTable(data.appointments || []);
                }
            })
            .catch(err => console.error('Error refreshing appointments:', err));
    }
    
    function refreshLeads() {
        // Fetch and update leads table
        fetch('/api/leads')
            .then(r => r.json())
            .then(data => {
                if (window.renderLeadsTable) {
                    window.renderLeadsTable(data.leads || []);
                }
            })
            .catch(err => console.error('Error refreshing leads:', err));
    }
    
    function showNotification(type, message) {
        // Disabled - using dashboard updates instead
        console.log(`[${type}] ${message}`);
    }
    
    function getNotificationIcon(type) {
        const icons = {
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        };
        return icons[type] || 'ℹ️';
    }
    
    function addActivityItem(type, message) {
        const activityFeed = document.getElementById('activity-feed');
        if (!activityFeed) return;
        
        const item = document.createElement('div');
        item.className = 'activity-item activity-' + type;
        item.innerHTML = `
            <span class="activity-time">${new Date().toLocaleTimeString()}</span>
            <span class="activity-message">${escapeHtml(message)}</span>
        `;
        
        activityFeed.insertBefore(item, activityFeed.firstChild);
        
        // Keep only last 10 items
        while (activityFeed.children.length > 10) {
            activityFeed.removeChild(activityFeed.lastChild);
        }
    }
    
    function refreshDashboard() {
        // Refresh analytics and recent activity
        fetch('/api/analytics')
            .then(r => r.json())
            .then(data => {
                // Update dashboard metrics
                updateDashboardMetrics(data);
            })
            .catch(err => console.error('Error refreshing dashboard:', err));
    }
    
    function updateDashboardMetrics(data) {
        // Update total calls
        const totalCallsEl = document.getElementById('total-calls');
        if (totalCallsEl && data.total_calls !== undefined) {
            totalCallsEl.textContent = data.total_calls;
        }
        
        // Update total leads
        const totalLeadsEl = document.getElementById('total-leads');
        if (totalLeadsEl && data.total_leads !== undefined) {
            totalLeadsEl.textContent = data.total_leads;
        }
        
        // Update total appointments
        const totalAppointmentsEl = document.getElementById('total-appointments');
        if (totalAppointmentsEl && data.total_appointments !== undefined) {
            totalAppointmentsEl.textContent = data.total_appointments;
        }
    }
})();
