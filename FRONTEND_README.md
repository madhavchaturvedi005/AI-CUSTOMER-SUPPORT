# Frontend Documentation

## Overview

The frontend is a modern, responsive web dashboard built with vanilla JavaScript, Tailwind CSS, and Chart.js. It provides real-time monitoring and management of the AI voice automation system with live updates via Server-Sent Events (SSE).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Web Dashboard                          │
│                  (index.html)                            │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
   ┌───▼────┐      ┌───▼────┐
   │  UI    │      │  Data  │
   │ Layer  │      │ Layer  │
   └───┬────┘      └───┬────┘
       │                │
       │         ┌──────▼──────┐
       │         │  REST API   │
       │         │  Endpoints  │
       │         └──────┬──────┘
       │                │
       │         ┌──────▼──────┐
       │         │     SSE     │
       │         │ Live Events │
       │         └─────────────┘
       │
   ┌───▼────────────────┐
   │   Chart.js         │
   │   Visualizations   │
   └────────────────────┘
```

## File Structure

### Core Files

**index.html** (641 lines)
- Main dashboard HTML structure
- Tab-based navigation system
- Responsive grid layouts
- Modal dialogs
- Form components
- Chart containers

**dashboard.js** (1,197 lines)
- Dashboard initialization and state management
- Tab switching logic
- Data fetching and API integration
- Chart rendering (Chart.js)
- Form submission handlers
- Configuration management
- Utility functions for formatting

**live_events.js** (300+ lines)
- Server-Sent Events (SSE) connection
- Real-time event handling
- Live transcript updates
- Call status monitoring
- Dashboard auto-refresh
- Notification system

## Features

### 1. Dashboard Tab

**Statistics Cards**
- Total Calls - Aggregate call count
- New Leads - Lead capture count
- Appointments - Scheduled appointments
- Avg Duration - Average call duration

**Charts**
- Call Volume (Line Chart) - Last 7 days trend
- Intent Distribution (Doughnut Chart) - Intent breakdown

**Live Components**
- Recent Activity Feed - Real-time activity stream
- Live Transcript - Active call transcription
- Active Call Banner - Current call status

### 2. Calls Tab

**Call History Table**
- Timestamp - When call occurred
- Caller - Phone number
- Intent - Detected intent
- Duration - Call length
- Status - Call status badge
- Actions - View details button

**Features**
- Sortable columns
- Refresh button
- Call detail modal
- Status color coding

### 3. Leads Tab

**Lead Management Table**
- Name - Lead name
- Phone - Contact number
- Email - Email address
- Score - Lead quality score (1-10)
- Budget - Budget indication
- Timeline - Purchase timeline
- Actions - View/edit buttons

**Features**
- Filter by score (High/Medium/Low)
- Color-coded score badges
- Refresh button
- Lead detail view

### 4. Appointments Tab

**Appointment Calendar**
- Card-based layout
- Customer information
- Service type
- Date and time
- Duration
- Status badges
- Notes display

**Features**
- Book new appointment button
- Booking modal form
- Refresh button
- Status color coding

**Booking Modal**
- Customer name input
- Phone number input
- Service type selection
- Date/time picker
- Notes textarea
- Validation

### 5. Configuration Tab

**Business Settings**
- Business Name - Company name configuration
- Business Hours - Operating hours setup
- AI Greeting - Custom greeting message
- Company Description - Business context (50-200 words)
- AI Personality - Tone and style settings
- Languages - Multi-language support toggles

**Features**
- Real-time word count for description
- Form validation
- Save confirmation
- Auto-load current settings

### 6. Documents Tab

**Knowledge Base Management**
- Document upload interface
- File list with metadata
- File type icons
- Upload date and size
- Delete functionality

**Supported Formats**
- PDF documents
- Word documents (.docx)
- Text files (.txt)

## Technology Stack

### Core Technologies

**HTML5**
- Semantic markup
- Accessibility features
- Form validation

**CSS**
- Tailwind CSS (CDN)
- Custom animations
- Responsive design
- Mobile-first approach

**JavaScript (ES6+)**
- Vanilla JavaScript (no framework)
- Async/await for API calls
- Event-driven architecture
- Modular code organization

### Libraries

**Tailwind CSS** (v3.x)
- Utility-first CSS framework
- Responsive utilities
- Component classes
- Custom color schemes

**Chart.js** (v4.x)
- Line charts for trends
- Doughnut charts for distribution
- Responsive charts
- Custom styling

**Font Awesome** (v6.4)
- Icon library
- 1000+ icons
- Consistent styling

## API Integration

### REST Endpoints

**GET /**
- Health check and system status

**GET /api/analytics**
- Dashboard statistics
- Call volume data
- Intent distribution
- Recent activity

**GET /api/calls**
- Call history list
- Pagination support
- Filter options

**GET /api/calls/{call_id}**
- Detailed call information
- Full transcript
- AI insights

**GET /api/leads**
- Lead list
- Filter by score
- Sort options

**GET /api/appointments**
- Appointment list
- Calendar view data

**POST /api/appointments**
- Create new appointment
- Validation
- Confirmation

**GET /api/config**
- Load current configuration
- All settings

**POST /api/config**
- Save configuration
- Type-specific updates

**POST /api/documents**
- Upload documents
- Multi-file support

**GET /api/documents**
- List uploaded documents
- Metadata

### Server-Sent Events (SSE)

**GET /api/events/live**
- Real-time event stream
- Auto-reconnection
- Event types:
  - `transcript` - Live transcription
  - `call_start` - New call initiated
  - `call_update` - Call metadata update
  - `call_end` - Call completed
  - `tool_execution` - Tool call result
  - `appointment_booked` - New appointment
  - `lead_created` - New lead captured
  - `complaint_logged` - Complaint received

## Real-Time Features

### Live Transcript
- Displays conversation in real-time
- Speaker identification (Caller/AI)
- Language detection display
- Auto-scroll to latest message
- Color-coded by speaker

### Active Call Banner
- Shows when call is active
- Displays current intent
- Shows detected language
- Lead score indicator
- Pulse animation

### Auto-Refresh
- Dashboard metrics update every 30s
- SSE for instant updates
- No page reload required
- Smooth transitions

## UI Components

### Cards
- Statistics cards with icons
- Appointment cards
- Activity feed items
- Document list items

### Tables
- Sortable headers
- Hover effects
- Action buttons
- Status badges
- Responsive layout

### Forms
- Input validation
- Error messages
- Success feedback
- Loading states
- Disabled states

### Modals
- Booking modal
- Call detail modal
- Lead detail modal
- Overlay backdrop
- Close on escape

### Badges
- Status badges (completed, in progress, failed)
- Score badges (color-coded 1-10)
- Intent badges
- Language badges

## Styling

### Color Scheme
- Primary: Blue (#3B82F6)
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Error: Red (#EF4444)
- Gray scale for text and backgrounds

### Responsive Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### Animations
- Fade in/out
- Slide in (notifications)
- Pulse (live indicators)
- Smooth transitions

## Code Organization

### dashboard.js Structure

```javascript
// Global variables
const API_BASE = window.location.origin;
let callVolumeChart = null;
let intentChart = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    refreshDashboard();
    setupFormHandlers();
});

// Tab management
function showTab(tabName) { }

// Chart initialization
function initializeCharts() { }

// Data fetching
async function refreshDashboard() { }
async function refreshCalls() { }
async function refreshLeads() { }
async function refreshAppointments() { }

// Form handlers
function setupFormHandlers() { }
async function saveConfiguration(type, data) { }

// Utility functions
function formatDateTime(dateString) { }
function formatDuration(seconds) { }
function getStatusBadge(status) { }
```

### live_events.js Structure

```javascript
// SSE connection
const es = new EventSource('/api/events/live');

// Event handlers
es.onmessage = function(e) {
    const event = JSON.parse(e.data);
    handleLiveEvent(event);
};

// Event routing
function handleLiveEvent(event) {
    switch (event.type) {
        case 'transcript': ...
        case 'call_start': ...
        case 'call_update': ...
    }
}

// DOM manipulation
function appendTranscriptRow() { }
function showActiveCallBanner() { }
function updateCallMetadata() { }
```

## Usage

### Opening the Dashboard

1. Start the backend server
2. Navigate to `http://localhost:5050/frontend/index.html`
3. Dashboard loads automatically

### Viewing Live Calls

1. Make a test call to your Twilio number
2. Active call banner appears
3. Live transcript updates in real-time
4. Intent and language detected automatically

### Managing Appointments

1. Click "Appointments" tab
2. Click "Book Appointment" button
3. Fill in customer details
4. Select date and time
5. Click "Confirm Booking"

### Configuring System

1. Click "Configuration" tab
2. Update business name
3. Set business hours
4. Customize greeting message
5. Add company description
6. Click "Save" on each section

### Uploading Documents

1. Click "Documents" tab
2. Click "Choose Files" button
3. Select PDF, Word, or text files
4. Files upload automatically
5. AI uses documents in conversations

## Browser Support

- Chrome 90+ (recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Lazy loading for charts
- Debounced API calls
- Efficient DOM updates
- Minimal re-renders
- SSE auto-reconnection

## Security

- CORS enabled for API calls
- Input sanitization
- XSS prevention
- CSRF protection (backend)
- Secure WebSocket connections

## Accessibility

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support
- Color contrast compliance

## Customization

### Changing Colors

Edit Tailwind classes in `index.html`:
```html
<!-- Primary color -->
<button class="bg-blue-600 hover:bg-blue-700">

<!-- Change to green -->
<button class="bg-green-600 hover:bg-green-700">
```

### Adding New Charts

```javascript
// In dashboard.js
const newChart = new Chart(ctx, {
    type: 'bar',
    data: { ... },
    options: { ... }
});
```

### Custom Event Handlers

```javascript
// In live_events.js
case 'custom_event':
    handleCustomEvent(event);
    break;
```

## Troubleshooting

### Dashboard Not Loading
- Check backend server is running
- Verify port 5050 is accessible
- Check browser console for errors

### Charts Not Displaying
- Verify Chart.js CDN is loaded
- Check canvas elements exist
- Inspect data format

### SSE Not Connecting
- Check `/api/events/live` endpoint
- Verify CORS settings
- Check browser console

### Forms Not Submitting
- Check form validation
- Verify API endpoint
- Check network tab for errors

## Development

### Local Development
```bash
# Start backend
python main.py

# Open in browser
open http://localhost:5050/frontend/index.html
```

### Testing
- Manual testing in browser
- Check responsive design
- Test all form submissions
- Verify SSE connection
- Test chart rendering

### Debugging
```javascript
// Enable console logging
console.log('Dashboard data:', data);

// Check SSE events
es.addEventListener('message', (e) => {
    console.log('SSE event:', e.data);
});
```

## Future Enhancements

- Dark mode support
- Export data to CSV/PDF
- Advanced filtering
- Custom date ranges
- User authentication
- Role-based access
- Mobile app version
- Offline support
- Push notifications
- Advanced analytics

## Support

For issues or questions:
1. Check browser console for errors
2. Verify API endpoints are responding
3. Check SSE connection status
4. Review network tab in DevTools
