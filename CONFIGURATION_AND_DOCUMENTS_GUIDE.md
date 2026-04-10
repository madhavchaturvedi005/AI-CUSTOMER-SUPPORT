# Configuration and Document Upload Guide

## Overview

The AI Voice Automation system now supports:
1. **Custom Greeting Configuration** - Set your own greeting message that the AI will use
2. **Document Upload** - Upload PDFs, DOCX, or TXT files that the AI will use to answer questions

## How It Works

### Custom Greeting Configuration

When you configure a custom greeting in the dashboard, it is:
1. **Saved to the database** (if PostgreSQL is connected)
2. **Stored in memory** for immediate use
3. **Used in the next phone call** - both in Twilio's initial greeting AND in the AI's instructions

### Document Upload

When you upload documents:
1. **Text is extracted** from PDF, DOCX, or TXT files
2. **Saved to database** in the `knowledge_base` table
3. **Added to AI instructions** so the AI can reference this information
4. **Used in conversations** to answer customer questions

## Example Use Case: Suresh Salon

### Step 1: Configure Custom Greeting

Go to the **Configuration** tab in the dashboard and set:

```
Hello, welcome to Suresh Salon! How can I help you today? 
I can understand English, Hindi, Tamil, and Telugu.
```

**What happens:**
- This greeting is saved to the database
- Next phone call will use this exact greeting
- The AI will introduce itself as Suresh Salon
- The AI knows it can speak 4 languages

### Step 2: Upload Business Information

Create a PDF file with your salon information:

**suresh_salon_info.pdf:**
```
SURESH SALON - BUSINESS INFORMATION

Services:
- Haircut: ₹300
- Hair Coloring: ₹1500
- Facial: ₹800
- Manicure: ₹400
- Pedicure: ₹500

Business Hours:
Monday - Saturday: 9:00 AM - 8:00 PM
Sunday: 10:00 AM - 6:00 PM

Location:
123 MG Road, Bangalore, Karnataka 560001

Contact:
Phone: +91 80 1234 5678
Email: contact@sureshsalon.com

Special Offers:
- First-time customers get 20% off
- Refer a friend and get ₹200 credit
- Monthly packages available

Booking Policy:
- Appointments preferred but walk-ins welcome
- Cancellation must be 24 hours in advance
- Payment accepted: Cash, Card, UPI
```

Upload this PDF in the **Documents** tab.

**What happens:**
- PDF text is extracted automatically
- Saved to knowledge base
- AI can now answer questions about:
  - Pricing
  - Services
  - Business hours
  - Location
  - Special offers
  - Booking policy

### Step 3: Test with a Phone Call

**Customer calls and asks:**

**Customer:** "Hi, what are your haircut prices?"

**AI Response:** "Hello! At Suresh Salon, our haircut service costs ₹300. Would you like to book an appointment?"

**Customer:** "What are your hours on Sunday?"

**AI Response:** "We're open on Sundays from 10:00 AM to 6:00 PM. Would you like to schedule a visit?"

**Customer:** "Do you have any offers for new customers?"

**AI Response:** "Yes! First-time customers get 20% off all services. We also have a referral program where you can earn ₹200 credit. Would you like to take advantage of this offer?"

## Technical Implementation

### Configuration Flow

```
Dashboard → POST /api/config → Database → Memory → Next Call
                                                      ↓
                                            Twilio Greeting
                                                      ↓
                                            AI Instructions
```

### Document Upload Flow

```
Dashboard → POST /api/documents → Extract Text → Database → AI Instructions
                                       ↓
                                  PyPDF2/python-docx
                                       ↓
                                  Plain Text
                                       ↓
                              Knowledge Base Table
                                       ↓
                              Added to AI Session
```

### Database Schema

#### business_config table
```sql
CREATE TABLE business_config (
    business_id VARCHAR(100) PRIMARY KEY,
    greeting_message TEXT,
    business_hours JSONB,
    ai_personality JSONB,
    supported_languages JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### knowledge_base table
```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY,
    filename VARCHAR(255),
    content TEXT,
    file_type VARCHAR(100),
    uploaded_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    metadata JSONB
);
```

## API Endpoints

### POST /api/config

Update business configuration.

**Request:**
```json
{
  "type": "greeting",
  "data": {
    "message": "Hello, welcome to Suresh Salon! How can I help you today? I can understand English, Hindi, Tamil, and Telugu."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration 'greeting' updated successfully and will be used in next call"
}
```

**Other configuration types:**

**Business Hours:**
```json
{
  "type": "business_hours",
  "data": {
    "weekday_start": "09:00",
    "weekday_end": "20:00",
    "weekend_start": "10:00",
    "weekend_end": "18:00"
  }
}
```

**AI Personality:**
```json
{
  "type": "personality",
  "data": {
    "tone": "friendly",
    "style": "conversational"
  }
}
```

### POST /api/documents

Upload documents for knowledge base.

**Request:**
```
Content-Type: multipart/form-data

files: [file1.pdf, file2.docx, file3.txt]
```

**Response:**
```json
{
  "success": true,
  "uploaded": 3,
  "files": ["suresh_salon_info.pdf", "services.docx", "policies.txt"],
  "message": "Uploaded 3 document(s). AI will use this information in conversations."
}
```

## Supported File Types

### PDF Files (.pdf)
- Extracted using PyPDF2
- All pages processed
- Text extracted and combined

### Word Documents (.docx)
- Extracted using python-docx
- All paragraphs processed
- Formatting preserved as plain text

### Text Files (.txt)
- Read directly
- UTF-8 encoding
- No processing needed

## Installation

### Install Document Processing Libraries

```bash
pip install PyPDF2 python-docx
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### Run Database Migration

```bash
# Run the knowledge base migration
python3 migrations/run_migration.py
```

This creates the `knowledge_base` table.

## Usage Examples

### Example 1: Restaurant

**Greeting:**
```
Welcome to Tasty Bites Restaurant! I'm your AI assistant. 
How can I help you today? I speak English, Hindi, and Tamil.
```

**Document (menu.pdf):**
```
MENU

Starters:
- Samosa: ₹50
- Spring Rolls: ₹80
- Paneer Tikka: ₹150

Main Course:
- Butter Chicken: ₹280
- Paneer Butter Masala: ₹220
- Biryani: ₹250

Desserts:
- Gulab Jamun: ₹60
- Ice Cream: ₹80

Delivery: Available within 5km
Minimum Order: ₹200
```

### Example 2: Medical Clinic

**Greeting:**
```
Hello, you've reached City Health Clinic. I'm here to help you 
schedule appointments and answer questions. I can assist you in 
English, Hindi, Telugu, and Bengali.
```

**Document (clinic_info.pdf):**
```
CITY HEALTH CLINIC

Doctors:
- Dr. Sharma (General Physician) - Mon-Fri 9AM-5PM
- Dr. Patel (Pediatrician) - Mon-Sat 10AM-6PM
- Dr. Kumar (Dentist) - Tue-Sat 2PM-8PM

Consultation Fees:
- General: ₹500
- Specialist: ₹800
- Follow-up: ₹300

Services:
- General Checkup
- Vaccinations
- Lab Tests
- Dental Care

Emergency: 24/7 available
Insurance: Accepted
```

### Example 3: Real Estate

**Greeting:**
```
Welcome to Prime Properties! I'm your virtual assistant ready to 
help you find your dream home. I can communicate in English, 
Hindi, Tamil, and Telugu.
```

**Document (properties.pdf):**
```
AVAILABLE PROPERTIES

2 BHK Apartment - Whitefield
- Price: ₹65 Lakhs
- Area: 1200 sq ft
- Floor: 5th
- Amenities: Gym, Pool, Parking

3 BHK Villa - Sarjapur
- Price: ₹1.2 Crores
- Area: 2000 sq ft
- Floors: 2
- Amenities: Garden, Parking, Security

1 BHK Studio - Koramangala
- Price: ₹45 Lakhs
- Area: 650 sq ft
- Floor: 3rd
- Amenities: Parking, Lift

Financing: Available through partner banks
Site Visits: Book online or call
```

## Testing

### Test Configuration

1. Open dashboard: `http://localhost:5050/frontend/index.html`
2. Go to **Configuration** tab
3. Enter custom greeting
4. Click **Save Greeting**
5. Make a test call
6. Verify the AI uses your greeting

### Test Document Upload

1. Create a PDF with business information
2. Go to **Documents** tab
3. Click **Choose Files** and select your PDF
4. Click upload
5. Make a test call
6. Ask questions about the information in the PDF
7. Verify the AI answers correctly

### Verify in Database

```bash
# Check configuration
psql voice_automation -c "SELECT * FROM business_config;"

# Check uploaded documents
psql voice_automation -c "SELECT filename, LENGTH(content), uploaded_at FROM knowledge_base;"

# View document content
psql voice_automation -c "SELECT filename, content FROM knowledge_base WHERE filename = 'suresh_salon_info.pdf';"
```

## Troubleshooting

### Issue: Greeting not updating

**Solution:**
1. Check if database is connected (look for "Connected to PostgreSQL" in logs)
2. Verify configuration was saved: `SELECT * FROM business_config;`
3. Restart the server to reload configuration
4. Make a new call (not an existing call)

### Issue: PDF text not extracted

**Solution:**
1. Install PyPDF2: `pip install PyPDF2`
2. Check if PDF is text-based (not scanned image)
3. Try converting PDF to text first
4. Check server logs for extraction errors

### Issue: AI not using uploaded information

**Solution:**
1. Verify document was uploaded successfully
2. Check knowledge base table: `SELECT * FROM knowledge_base;`
3. Restart server to reload knowledge base
4. Make a new call to test
5. Ask specific questions that are in the document

### Issue: Document upload fails

**Solution:**
1. Check file size (max 10MB recommended)
2. Verify file type (PDF, DOCX, TXT only)
3. Check server logs for errors
4. Ensure `documents/` directory exists
5. Check file permissions

## Best Practices

### Greeting Messages

✅ **Good:**
- Clear business name
- Friendly tone
- Mention supported languages
- Keep it concise (2-3 sentences)

❌ **Avoid:**
- Too long (>5 sentences)
- Technical jargon
- Multiple questions
- Confusing language

### Document Content

✅ **Good:**
- Clear headings and sections
- Bullet points for lists
- Specific prices and details
- Contact information
- Business hours
- Policies and terms

❌ **Avoid:**
- Images without text
- Complex tables
- Scanned documents (use OCR first)
- Irrelevant information
- Outdated information

### File Organization

```
documents/
├── business_info.pdf       # General business information
├── services_pricing.pdf    # Services and pricing
├── policies.pdf            # Policies and terms
├── faq.pdf                 # Frequently asked questions
└── special_offers.pdf      # Current promotions
```

## Advanced Features

### Multiple Documents

Upload multiple documents - they will all be combined into the knowledge base:

```javascript
// The AI will have access to all uploaded documents
Document 1: Business hours and location
Document 2: Services and pricing
Document 3: Policies and terms
Document 4: Special offers
```

### Update Documents

To update information:
1. Upload new document with same filename (it will be added, not replaced)
2. Or mark old documents as inactive in database
3. Or delete old documents and upload new ones

### Search Knowledge Base

```sql
-- Search for specific information
SELECT filename, content 
FROM knowledge_base 
WHERE content ILIKE '%haircut%';

-- Full text search
SELECT filename, ts_rank(to_tsvector('english', content), query) AS rank
FROM knowledge_base, to_tsquery('english', 'haircut & price') query
WHERE to_tsvector('english', content) @@ query
ORDER BY rank DESC;
```

## Summary

✅ **Configuration works** - Custom greetings are used in real calls
✅ **Document upload works** - PDFs are processed and used by AI
✅ **Database integration** - Everything is saved and persisted
✅ **Real-time updates** - Changes apply to next call immediately
✅ **Multi-language support** - Works with all 5 supported languages

Your AI assistant is now fully customizable and can answer questions specific to your business!
