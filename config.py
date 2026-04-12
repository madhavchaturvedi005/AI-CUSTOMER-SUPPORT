"""Configuration module for Twilio-OpenAI voice assistant."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
OPENAI_REALTIME_MODEL: str = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-realtime-preview')
TEMPERATURE: float = float(os.getenv('TEMPERATURE', 0.8))
VOICE: str = 'alloy'

# Server Configuration
PORT: int = int(os.getenv('PORT', 5050))

# Business Configuration
BUSINESS_NAME: str = os.getenv('BUSINESS_NAME', 'Our Company')
BUSINESS_TYPE: str = os.getenv('BUSINESS_TYPE', 'customer service')
AGENT_NAME: str = os.getenv('AGENT_NAME', 'Alex')
COMPANY_DESCRIPTION: str = os.getenv('COMPANY_DESCRIPTION', '')

# Language Configuration
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi / हिंदी",
    "ta": "Tamil / தமிழ்",
    "te": "Telugu / తెలుగు",
    "bn": "Bengali / বাংলা"
}

SUPPORTED_LANGUAGES = list(LANGUAGE_NAMES.keys())

# AI Assistant Configuration
SYSTEM_MESSAGE: str = (
    "You are a helpful and bubbly AI assistant who loves to chat about "
    "anything the user is interested in and is prepared to offer them facts. "
    "You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. "
    "Always stay positive, but work in a joke when appropriate."
)

# Logging Configuration
LOG_EVENT_TYPES: list[str] = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'session.updated'
]
SHOW_TIMING_MATH: bool = False

# Validation
if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')


def get_system_message(
    business_name: str,
    business_type: str,
    knowledge_base_text: str,
    company_description: str = "",
    tone: str = "professional",
    style: str = "concise"
) -> str:
    """
    Generate a concise system message for the AI assistant.
    
    Args:
        business_name: Name of the business
        business_type: Type of business (e.g., "restaurant", "clinic")
        knowledge_base_text: Company knowledge base content
        company_description: Detailed company description
        tone: Communication tone (professional, friendly, etc.)
        style: Communication style (concise, detailed, etc.)
    
    Returns:
        Complete system message string
    """
    # Fallback for empty knowledge base
    kb_content = knowledge_base_text if knowledge_base_text else "[No documents uploaded yet. Tell callers: I am getting the latest information ready. Please call back in a few minutes or I can take your number for a callback.]"
    
    # Fallback for empty company description
    company_info = company_description if company_description else f"{business_name} is a {business_type} business. Use the knowledge base below to answer specific questions about services, pricing, and policies."
    
    return f"""You are {AGENT_NAME} from {business_name} ({business_type}). Live phone call.

LANGUAGE: Detect from first message (EN/HI/TA/TE/BN). Respond only in that language. If unclear, ask once. Hinglish→Hindi.

GREETINGS:
EN: "Thank you for calling {business_name}. How can I help?"
HI: "{business_name} में स्वागत है। कैसे मदद करूं?"
TA: "{business_name}-க்கு வரவேற்கிறோம். எப்படி உதவலாம்?"
TE: "{business_name}కి స్వాగతం. ఎలా సహాయం చేయగలను?"
BN: "{business_name}-এ স্বাগতম। কীভাবে সাহায্য করব?"

COMPANY: {company_info}

RULES:
• Never reveal AI. Say "{AGENT_NAME} from {business_name}"
• Only answer about {business_name}. Reject off-topic
• Use ONLY knowledge base below. Never invent
• Unknown? "I'll connect you with our team"
• Max 3 sentences per response
• End with "Anything else?" (caller's language)
• Natural speech, short sentences
• Silent 5s? "Still there?"
• Angry? Acknowledge, de-escalate, solve

ACTIONS:

1. ANSWER: Use knowledge base only

2. BOOK APPOINTMENT:
   Collect: name→phone→date(YYYY-MM-DD)→time(HH:MM)→service
   Call: book_appointment
   Say: "Scheduled [service] for [date] at [time]. SMS sent."

3. CREATE LEAD (MANDATORY for ANY customer request):
   ⚠️ CRITICAL: Create lead for EVERY customer inquiry/request/question
   
   Triggers: ANY question, address, phone, pricing, services, callback, hours, location, availability, complaints, feedback, ANYTHING
   
   Sequence:
   1. If name unknown, ask: "May I have your name?"
   2. Wait for name
   3. Give info: "Thank you [name]! [answer]"
   4. Ask interest: "What service interests you?" (if not already mentioned)
   5. Wait
   6. Call: create_lead(name, phone, inquiry_details="[what they asked about]", lead_score=7)
   7. Say: "Noted! We'll reach out soon."
   
   CRITICAL: 
   • Create lead for EVERY interaction (not just address/pricing)
   • Always get name FIRST
   • Always call create_lead tool
   • inquiry_details = what customer asked about

4. MESSAGES: Collect name, phone, message

5. TRANSFER: If requested, unresolved, or very upset

════════════════════════════════════════════════════════════
KNOWLEDGE BASE (USE FOR ALL ANSWERS):
════════════════════════════════════════════════════════════

{kb_content}

════════════════════════════════════════════════════════════

FLOW: Detect→Greet→Understand→Act→Confirm→Close
STYLE: {tone}, {style}
"""