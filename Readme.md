# AI Customer Support - Voice Assistant

A production-ready AI-powered voice assistant for customer support using OpenAI Realtime API, Twilio, and PostgreSQL. Supports 5 languages with automatic detection, real-time transcription, and comprehensive analytics dashboard.

## 🌟 Features

### Core Capabilities
- ✅ **Real-time Voice Conversations** - Natural phone conversations using OpenAI Realtime API
- ✅ **5 Language Support** - English, Hindi, Tamil, Telugu, Bengali with automatic detection
- ✅ **Call Transcription** - Real-time transcription saved to database
- ✅ **AI Insights** - Automatic sentiment analysis, key points extraction, and action items
- ✅ **Intent Detection** - Automatic detection of caller intent with clarification
- ✅ **Call Analytics** - Comprehensive dashboard with metrics and trends
- ✅ **Knowledge Base** - Upload documents (PDF, DOCX, TXT) for AI context
- ✅ **Configurable AI** - Customize greeting, personality, and company description
- ✅ **Cloud Database** - Aiven PostgreSQL for data persistence
- ✅ **Call History** - Complete conversation logs with timestamps

### Dashboard Features
- 📊 Real-time analytics and metrics
- 📞 Call history with detailed transcripts
- 💬 AI-generated insights for each call
- 📈 Intent distribution charts
- 🎯 Lead management
- 📅 Appointment tracking
- ⚙️ Configuration management
- 📚 Document upload for knowledge base

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (or Aiven account)
- Redis
- Twilio account
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT.git
cd AI-CUSTOMER-SUPPORT
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Aiven PostgreSQL (Cloud Database)
DB_HOST=your-service.aivencloud.com
DB_PORT=14641
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=your_password
DB_SSLMODE=require

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Server
PORT=5050
```

4. **Run database migrations**
```bash
# Using Aiven PostgreSQL
psql "postgres://user:pass@host:port/db?sslmode=require" -f migrations/001_initial_schema.sql
psql "postgres://user:pass@host:port/db?sslmode=require" -f migrations/002_knowledge_base.sql
psql "postgres://user:pass@host:port/db?sslmode=require" -f migrations/003_company_description.sql
```

5. **Start the server**
```bash
python3 main.py
```

6. **Access the dashboard**
```
http://localhost:5050/frontend/index.html
```

## 📱 Twilio Setup

1. Create a Twilio account at https://www.twilio.com
2. Get a phone number with voice capabilities
3. Configure webhook URL:
   - Voice: `https://your-domain.com/incoming-call`
   - Method: GET

## 🗄️ Database Setup

### Option 1: Aiven PostgreSQL (Recommended for Production)

1. Sign up at https://aiven.io (free $300 credits)
2. Create PostgreSQL service (Hobbyist plan is free)
3. Copy connection details to .env
4. Run migrations (see Installation step 4)

**Benefits:**
- ✅ Data persists across PC shutdowns
- ✅ Automatic daily backups
- ✅ 99.99% uptime
- ✅ Free tier available

See [AIVEN_POSTGRESQL_SETUP.md](AIVEN_POSTGRESQL_SETUP.md) for detailed guide.

### Option 2: Local PostgreSQL

```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or
sudo apt-get install postgresql  # Linux

# Create database
createdb voice_automation

# Update .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_automation
DB_USER=your_username
```

## 🌍 Multilingual Support

The system automatically detects and responds in the caller's language:

- **English** - Default
- **Hindi / हिंदी** - Automatic detection
- **Tamil / தமிழ்** - Automatic detection
- **Telugu / తెలుగు** - Automatic detection
- **Bengali / বাংলা** - Automatic detection

### How it works:
1. Caller speaks in their preferred language
2. AI detects language from first message
3. AI responds entirely in that language
4. Language consistency maintained throughout call

See [MULTILINGUAL_SYSTEM_IMPLEMENTATION.md](MULTILINGUAL_SYSTEM_IMPLEMENTATION.md) for details.

## 📊 Dashboard

Access the dashboard at `http://localhost:5050/frontend/index.html`

### Tabs:
1. **Overview** - Real-time metrics and charts
2. **Call History** - All calls with transcripts and insights
3. **Leads** - Captured lead information
4. **Appointments** - Scheduled appointments
5. **Configuration** - Customize AI behavior
6. **Documents** - Upload knowledge base documents

### Configuration Options:
- **Greeting Message** - Custom phone greeting
- **Company Description** - Business context for AI (50-200 words recommended)
- **AI Personality** - Tone (Professional, Friendly, Casual) and Style (Concise, Detailed)
- **Business Hours** - Operating hours
- **Languages** - All 5 languages enabled by default

## 🔧 API Endpoints

### Call Management
- `GET /incoming-call` - Twilio webhook for incoming calls
- `GET /api/calls` - List all calls
- `GET /api/calls/{call_id}` - Get call details with transcript and insights

### Analytics
- `GET /api/analytics` - Dashboard analytics and metrics

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration

### Documents
- `GET /api/documents` - List uploaded documents
- `POST /api/documents` - Upload documents for knowledge base

### Debug
- `GET /api/system-prompt` - View current AI system prompt

## 🏗️ Architecture

```
┌─────────────┐
│   Twilio    │ ← Phone calls
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────┐
│      FastAPI Server             │
│  ┌──────────────────────────┐  │
│  │  WebSocket Handler       │  │
│  │  (Twilio ↔ OpenAI)      │  │
│  └──────────────────────────┘  │
│  ┌──────────────────────────┐  │
│  │  Call Manager            │  │
│  │  - Language Detection    │  │
│  │  - Intent Detection      │  │
│  │  - Conversation History  │  │
│  └──────────────────────────┘  │
└─────────┬───────────────────────┘
          │
          ↓
┌─────────────────────────────────┐
│   Aiven PostgreSQL (Cloud)      │
│   - Calls & Transcripts         │
│   - Leads & Appointments        │
│   - Configuration               │
│   - Knowledge Base              │
└─────────────────────────────────┘
```

## 📝 Key Files

- `main.py` - FastAPI server and WebSocket handlers
- `config.py` - Configuration and multilingual system message
- `database.py` - PostgreSQL operations
- `call_manager.py` - Call lifecycle management
- `handlers.py` - Twilio/OpenAI WebSocket handlers
- `intent_detector.py` - Intent detection logic
- `language_manager.py` - Language detection and management
- `frontend/` - Dashboard HTML/JS

## 🔐 Security

- ✅ SSL/TLS encryption for database connections
- ✅ Environment variables for sensitive data
- ✅ .env file excluded from git
- ✅ Secure password authentication
- ✅ API key protection

## 🐛 Troubleshooting

### Connection Issues
```bash
# Test database connection
psql "your_connection_string" -c "SELECT version();"

# Test server
curl http://localhost:5050/api/analytics
```

### Timezone Errors
- Ensure all datetime objects are timezone-aware
- Database automatically handles timezone conversion

### Call Not Saving
- Check server logs for errors
- Verify database connection
- Ensure migrations ran successfully

## 📚 Documentation

- [Aiven PostgreSQL Setup](AIVEN_POSTGRESQL_SETUP.md)
- [Multilingual System](MULTILINGUAL_SYSTEM_IMPLEMENTATION.md)
- [Frontend Updates](FRONTEND_MULTILINGUAL_UPDATE.md)
- [Transcript Saving Fix](TRANSCRIPT_AND_GREETING_FIX.md)
- [Database Migration](AIVEN_MIGRATION_COMPLETE.md)

## 🚧 Known Limitations

- ⚠️ Appointment booking requires manual integration (AI can discuss but not save)
- ⚠️ Call transfer to human agents not implemented
- ⚠️ SMS notifications not configured

## 🛣️ Roadmap

- [ ] Function calling for appointment booking
- [ ] SMS notifications via Twilio
- [ ] Email integration
- [ ] CRM integration (Salesforce, HubSpot)
- [ ] Multi-tenant support
- [ ] Advanced analytics and reporting
- [ ] Call recording storage
- [ ] Voicemail handling

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Email: madhavchaturvedi005@gmail.com

## 🙏 Acknowledgments

- OpenAI Realtime API
- Twilio Voice API
- Aiven PostgreSQL
- FastAPI Framework

## 📊 Stats

- **Languages**: Python, JavaScript, HTML, CSS
- **Database**: PostgreSQL (Aiven)
- **Cache**: Redis
- **API**: OpenAI Realtime API, Twilio Voice
- **Framework**: FastAPI
- **Frontend**: Vanilla JS, Tailwind CSS

---

Built with ❤️ by Madhav Chaturvedi
