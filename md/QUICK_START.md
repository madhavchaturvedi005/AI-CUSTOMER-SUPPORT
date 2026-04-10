# Quick Start Guide - Configuration & Documents

## ✅ Database Setup Complete!

Your database is now ready with:
- ✅ `knowledge_base` table created
- ✅ Full-text search indexes
- ✅ PostgreSQL user: `madhavchaturvedi`

## 🚀 How to Use

### Option 1: Demo Mode (No Database - Recommended for Testing)

Just start the server - configuration and documents will work in memory:

```bash
python3 main.py
```

Then open: `http://localhost:5050/frontend/index.html`

### Option 2: Production Mode (With Database)

Enable database in `.env`:

```bash
# Edit .env file
USE_REAL_DB=true
```

Then start:

```bash
python3 main.py
```

## 📝 Configure Your Greeting

1. Open dashboard: `http://localhost:5050/frontend/index.html`
2. Go to **Configuration** tab
3. Enter your greeting:
   ```
   Hello, welcome to Suresh Salon! How can I help you today? 
   I can understand English, Hindi, Tamil, and Telugu.
   ```
4. Click **Save Greeting**
5. ✅ Next phone call will use this greeting!

## 📄 Upload Business Documents

1. Create a text file or PDF with your business info:

**Example: `business_info.txt`**
```
SURESH SALON

Services:
- Haircut: ₹300
- Hair Coloring: ₹1500
- Facial: ₹800
- Manicure: ₹400

Business Hours:
Monday - Saturday: 9:00 AM - 8:00 PM
Sunday: 10:00 AM - 6:00 PM

Location:
123 MG Road, Bangalore

Special Offers:
- First-time customers: 20% off
- Refer a friend: ₹200 credit

Contact:
Phone: +91 80 1234 5678
```

2. Go to **Documents** tab in dashboard
3. Click **Choose Files**
4. Select your file
5. Click upload
6. ✅ AI can now answer questions from this document!

## 🧪 Test It

### Test Configuration

```bash
# Make a test call to your Twilio number
# The AI will use your custom greeting!
```

### Test Document Upload

**Customer asks:** "What are your haircut prices?"

**AI answers:** "At Suresh Salon, our haircut service costs ₹300. Would you like to book an appointment?"

## 🔧 Troubleshooting

### If you see "role postgres does not exist"

Already fixed! Your `.env` now uses `madhavchaturvedi` as the database user.

### If migration fails

Run manually:
```bash
DB_USER=madhavchaturvedi python3 migrations/run_migration.py 002_knowledge_base.sql
```

### If you want to use demo mode

Just set in `.env`:
```
USE_REAL_DB=false
```

Everything will work in memory (no database needed).

## 📊 Verify Database

Check if configuration is saved:
```bash
psql voice_automation -c "SELECT * FROM business_config;"
```

Check uploaded documents:
```bash
psql voice_automation -c "SELECT filename, LENGTH(content), uploaded_at FROM knowledge_base;"
```

## 🎉 You're Ready!

1. ✅ Database is set up
2. ✅ Configuration works
3. ✅ Document upload works
4. ✅ AI will use your custom greeting
5. ✅ AI can answer questions from your documents

Just configure your greeting and upload your business documents in the dashboard!

## 📚 More Information

- **Full Guide**: `CONFIGURATION_AND_DOCUMENTS_GUIDE.md`
- **System Architecture**: `SYSTEM_ARCHITECTURE.md`
- **Database Integration**: `FRONTEND_DATABASE_INTEGRATION.md`
