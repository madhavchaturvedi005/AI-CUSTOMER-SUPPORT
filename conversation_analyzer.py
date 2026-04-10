"""Analyze call conversations and extract structured data using AI."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import openai
from config import OPENAI_API_KEY

class ConversationAnalyzer:
    """Analyzes call conversations and extracts appointments, leads, and insights."""
    
    def __init__(self, api_key: str = OPENAI_API_KEY):
        """Initialize the conversation analyzer."""
        self.client = openai.OpenAI(api_key=api_key)
    
    async def analyze_conversation(
        self,
        conversation_history: List[Dict[str, Any]],
        caller_phone: str,
        call_duration_seconds: int
    ) -> Dict[str, Any]:
        """
        Analyze a complete conversation and extract structured data.
        
        Args:
            conversation_history: List of conversation turns with speaker and text
            caller_phone: Caller's phone number
            call_duration_seconds: Duration of the call in seconds
            
        Returns:
            Dictionary with appointments, leads, and call insights
        """
        # Format conversation for AI analysis
        conversation_text = self._format_conversation(conversation_history)
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(conversation_text, caller_phone, call_duration_seconds)
        
        try:
            # Call OpenAI to analyze
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing customer service call transcripts and extracting structured data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            print(f"📊 Conversation analysis complete:")
            print(f"   Appointments: {len(result.get('appointments', []))}")
            print(f"   Leads: {len(result.get('leads', []))}")
            print(f"   Intent: {result.get('call_insights', {}).get('primary_intent')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error analyzing conversation: {e}")
            import traceback
            traceback.print_exc()
            return {
                "appointments": [],
                "leads": [],
                "call_insights": {
                    "primary_intent": "unknown",
                    "sentiment": "neutral",
                    "resolution_status": "unknown",
                    "key_topics": [],
                    "action_items": []
                }
            }
    
    def _format_conversation(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Format conversation history into readable text."""
        lines = []
        for turn in conversation_history:
            speaker = turn.get('speaker', 'unknown')
            text = turn.get('text', '')
            
            # Normalize speaker names
            if speaker in ['caller', 'customer', 'user']:
                speaker_label = "Customer"
            elif speaker in ['assistant', 'agent', 'ai']:
                speaker_label = "Agent"
            else:
                speaker_label = speaker.title()
            
            lines.append(f"{speaker_label}: {text}")
        
        return "\n".join(lines)
    
    def _create_analysis_prompt(
        self,
        conversation_text: str,
        caller_phone: str,
        call_duration_seconds: int
    ) -> str:
        """Create the analysis prompt for OpenAI."""
        
        # Calculate a reasonable default appointment time (tomorrow at 10 AM)
        default_time = datetime.now(timezone.utc) + timedelta(days=1)
        default_time = default_time.replace(hour=10, minute=0, second=0, microsecond=0)
        
        return f"""Analyze this customer service call transcript and extract structured data.

CALL METADATA:
- Caller Phone: {caller_phone}
- Call Duration: {call_duration_seconds} seconds
- Default Appointment Time (if not specified): {default_time.isoformat()}

CONVERSATION TRANSCRIPT:
{conversation_text}

EXTRACT THE FOLLOWING DATA:

1. APPOINTMENTS - Look for any appointment bookings, rescheduling, or confirmations
   - Extract: customer_name, customer_phone, service_type, appointment_datetime, notes
   - If the agent said "I've scheduled", "I've booked", "appointment confirmed", etc., there IS an appointment
   - If date/time not explicitly mentioned, use the default time provided above
   - Parse dates like "tomorrow", "next week", "Friday" into ISO format
   - If only time mentioned (e.g., "2 PM"), use tomorrow's date

2. LEADS - Look for sales inquiries or information requests
   - Extract: name, phone, email, inquiry_details, budget_indication, timeline, lead_score (1-10)
   - Lead score based on: urgency, budget mentioned, decision authority, engagement level
   - High score (8-10): Ready to buy, has budget, decision maker
   - Medium score (4-7): Interested, needs more info, timeline unclear
   - Low score (1-3): Just browsing, no budget, far future

3. CALL INSIGHTS - Analyze the overall call
   - primary_intent: appointment_booking, sales_inquiry, support_request, complaint, general_inquiry
   - sentiment: positive, neutral, negative
   - resolution_status: resolved, pending, escalated, unresolved
   - key_topics: List of main topics discussed (max 5)
   - action_items: What needs to be done next (max 3)
   - customer_satisfaction: satisfied, neutral, unsatisfied (based on tone and resolution)

IMPORTANT RULES:
- If customer name not mentioned, use "Customer" or extract from context
- Always use the caller_phone provided in metadata
- For appointment_datetime, ALWAYS return ISO 8601 format: "2026-04-12T14:00:00Z"
- If no appointments were booked, return empty appointments array
- If no lead information collected, return empty leads array
- Be conservative - only extract data that's clearly present in the conversation

Return ONLY valid JSON in this exact format:
{{
  "appointments": [
    {{
      "customer_name": "John Doe",
      "customer_phone": "{caller_phone}",
      "service_type": "Consultation",
      "appointment_datetime": "2026-04-12T14:00:00Z",
      "duration_minutes": 30,
      "notes": "First-time customer, interested in premium package"
    }}
  ],
  "leads": [
    {{
      "name": "John Doe",
      "phone": "{caller_phone}",
      "email": "john@example.com",
      "inquiry_details": "Interested in premium package pricing",
      "budget_indication": "high",
      "timeline": "immediate",
      "lead_score": 8
    }}
  ],
  "call_insights": {{
    "primary_intent": "appointment_booking",
    "sentiment": "positive",
    "resolution_status": "resolved",
    "key_topics": ["appointment booking", "service pricing", "availability"],
    "action_items": ["Send confirmation SMS", "Prepare consultation materials"],
    "customer_satisfaction": "satisfied"
  }}
}}"""
    
    def parse_datetime_from_text(self, text: str) -> Optional[datetime]:
        """Parse natural language datetime into datetime object."""
        text_lower = text.lower()
        now = datetime.now(timezone.utc)
        
        # Tomorrow
        if "tomorrow" in text_lower:
            result = now + timedelta(days=1)
            # Extract time if mentioned
            if "morning" in text_lower:
                return result.replace(hour=10, minute=0, second=0, microsecond=0)
            elif "afternoon" in text_lower:
                return result.replace(hour=14, minute=0, second=0, microsecond=0)
            elif "evening" in text_lower:
                return result.replace(hour=18, minute=0, second=0, microsecond=0)
            else:
                return result.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Next week
        if "next week" in text_lower:
            return (now + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        # Today
        if "today" in text_lower:
            return now.replace(hour=14, minute=0, second=0, microsecond=0)
        
        # Default to tomorrow 10 AM
        return (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
