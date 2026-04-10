# Lead Capture Enhancement - Automatic Lead Creation

## What Changed

Updated the AI agent to **automatically create leads** when customers show interest by asking for basic business information.

---

## 🎯 New Trigger Points for Lead Creation

The AI agent will now create a lead when the caller:

### 1. **Asks for Address/Location**
```
Caller: "Where are you located?"
Caller: "What's your address?"
Caller: "How do I get to your office?"
```

### 2. **Asks for Phone Number**
```
Caller: "What's your phone number?"
Caller: "How can I reach you?"
Caller: "Can I have your contact number?"
```

### 3. **Shows Interest in Services**
```
Caller: "Tell me about your services"
Caller: "I'm interested in..."
Caller: "What do you offer?"
```

### 4. **Asks About Pricing**
```
Caller: "How much does it cost?"
Caller: "What are your prices?"
Caller: "Do you have packages?"
```

### 5. **Requests Callback**
```
Caller: "Can someone call me back?"
Caller: "I'd like to speak to someone"
```

---

## 📋 How It Works

### Step-by-Step Flow:

**Example: Caller asks for address**

```
👤 Caller: "What's your address?"

🤖 Agent: 
  1. Answers the question first
     "We're located at 123 Main Street, Downtown."
  
  2. Then asks for name
     "I'd love to help you further. May I have your name please?"

👤 Caller: "Sure, it's John Smith"

🤖 Agent:
  3. Asks for phone (if not already captured from caller ID)
     "Great! And what's the best number to reach you?"

👤 Caller: "+1234567890"

🤖 Agent:
  4. Asks about interest
     "What service are you interested in?"

👤 Caller: "I'm looking for a consultation"

🤖 Agent:
  5. Creates lead automatically using create_lead tool
  6. Confirms
     "Thank you John. I've noted your interest in a consultation. 
      Our team will reach out to you soon."

✅ Result:
  - Lead created in database
  - Dashboard updated in real-time
  - Lead score calculated
  - Ready for follow-up
```

---

## 🌍 Multilingual Support

The agent asks for name in the caller's language:

- **English**: "I'd love to help you further. May I have your name please?"
- **Hindi**: "मैं आपकी और सहायता करना चाहूंगा/चाहूंगी। कृपया अपना नाम बताएं?"
- **Tamil**: "நான் உங்களுக்கு மேலும் உதவ விரும்புகிறேன். உங்கள் பெயர் என்ன?"
- **Telugu**: "నేను మీకు మరింత సహాయం చేయాలనుకుంటున్నాను. దయచేసి మీ పేరు చెప్పండి?"
- **Bengali**: "আমি আপনাকে আরও সাহায্য করতে চাই। আপনার নাম কী?"

---

## 📊 What Gets Captured

When a lead is created, the system saves:

1. **Name** (required) - Collected from caller
2. **Phone** (required) - From caller ID or asked
3. **Email** (optional) - Asked if caller provides
4. **Inquiry Details** - What they asked about
5. **Lead Score** - Automatically calculated (1-10)
6. **Source** - "voice_call"
7. **Timestamp** - When lead was created

---

## 💡 Why This Matters

### Before:
❌ Caller asks for address → Gets address → Hangs up → Lost opportunity  
❌ No way to follow up  
❌ No record of interest  

### After:
✅ Caller asks for address → Gets address → Agent captures name → Lead created  
✅ Can follow up later  
✅ Lead tracked in dashboard  
✅ Never lose a potential customer  

---

## 🎯 Business Impact

### Increased Lead Capture Rate
- Every information request becomes a lead opportunity
- Proactive name collection
- Natural conversation flow

### Better Follow-Up
- All interested callers captured
- Even if they don't book immediately
- Team can reach out later

### Data-Driven Insights
- Track which questions lead to conversions
- Understand customer journey
- Optimize marketing

---

## 🔄 Complete Flow Examples

### Example 1: Address Request

```
📞 Call starts

👤: "Hi, what's your address?"

🤖: "We're located at 123 Main Street in Downtown. 
     I'd love to help you further. May I have your name please?"

👤: "It's Sarah"

🤖: "Thank you Sarah! And what's the best number to reach you?"

👤: "555-1234"

🤖: "Perfect! What service are you interested in?"

👤: "I'm thinking about a consultation"

🤖: "Thank you Sarah. I've noted your interest in a consultation. 
     Our team will reach out to you soon. Is there anything else 
     I can help you with today?"

✅ Lead created with:
   - Name: Sarah
   - Phone: 555-1234
   - Interest: Consultation
   - Score: 7/10
```

### Example 2: Phone Number Request

```
📞 Call starts

👤: "Can I get your phone number?"

🤖: "Of course! You can reach us at 555-BUSINESS. 
     May I have your name please?"

👤: "Mike Johnson"

🤖: "Great Mike! What brings you to call today?"

👤: "Just wanted to know more about your services"

🤖: "I'd be happy to help! What specific service are you 
     interested in?"

👤: "Your premium package"

🤖: "Excellent choice! Thank you Mike. I've noted your interest 
     in our premium package. Our team will call you back to 
     discuss the details. Is there anything else?"

✅ Lead created with:
   - Name: Mike Johnson
   - Phone: (from caller ID)
   - Interest: Premium package
   - Score: 8/10
```

### Example 3: Pricing Inquiry

```
📞 Call starts

👤: "How much do your services cost?"

🤖: "Our basic package starts at $99, and we have premium options 
     up to $299. May I have your name to provide more details?"

👤: "Lisa"

🤖: "Thank you Lisa! Which package interests you most?"

👤: "The premium one sounds good"

🤖: "Great choice! I've noted your interest in our premium package. 
     Our team will reach out with detailed pricing and options. 
     Can I help with anything else?"

✅ Lead created with:
   - Name: Lisa
   - Phone: (from caller ID)
   - Interest: Premium package pricing
   - Score: 8/10
```

---

## 🚀 How to Use

### 1. Restart Your Server
The changes are in `config.py`, so restart to apply:
```bash
python3 main.py
```

### 2. Test It
Call your Twilio number and say:
- "What's your address?"
- "Can I have your phone number?"
- "How much does it cost?"

The agent should:
1. Answer your question
2. Ask for your name
3. Collect information
4. Create a lead

### 3. Check Dashboard
Go to the "Leads" tab - you should see the new lead appear in real-time!

---

## 📈 Expected Results

### More Leads Captured
- Every inquiry becomes a lead opportunity
- Proactive information collection
- Natural, non-pushy approach

### Better Conversion
- Follow up with interested callers
- Don't lose warm leads
- Track interest over time

### Improved ROI
- Maximize value from every call
- Better marketing attribution
- Data-driven decisions

---

## 🎓 Key Principles

### 1. **Answer First, Then Capture**
Always answer the caller's question before asking for information. This builds trust.

### 2. **Natural Flow**
The name request feels natural: "I'd love to help you further. May I have your name?"

### 3. **Multilingual**
Works in all 6 supported languages automatically.

### 4. **Non-Intrusive**
If caller doesn't want to share, agent doesn't push. But most will share when asked politely.

### 5. **Automatic**
Agent decides when to create lead - no manual intervention needed.

---

## 📝 Summary

Your AI agent now automatically creates leads when customers:
- Ask for address
- Ask for phone number  
- Show interest in services
- Ask about pricing
- Request callback

This ensures you never lose a potential customer and can follow up with everyone who shows interest!
