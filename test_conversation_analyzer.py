"""Test the conversation analyzer."""

import asyncio
from datetime import datetime, timezone
from conversation_analyzer import ConversationAnalyzer

async def test_analyzer():
    """Test conversation analysis with sample conversations."""
    
    print("🧪 Testing Conversation Analyzer\n")
    print("="*60)
    
    analyzer = ConversationAnalyzer()
    
    # Test 1: Appointment booking conversation
    print("\nTest 1: Appointment Booking Conversation")
    print("-"*60)
    
    conversation1 = [
        {"speaker": "assistant", "text": "Thank you for calling. How can I help you today?"},
        {"speaker": "customer", "text": "Hi, I'd like to book an appointment for a haircut"},
        {"speaker": "assistant", "text": "I'd be happy to help you book a haircut. What's your name?"},
        {"speaker": "customer", "text": "My name is John Doe"},
        {"speaker": "assistant", "text": "Great! And what day works best for you?"},
        {"speaker": "customer", "text": "How about tomorrow at 2 PM?"},
        {"speaker": "assistant", "text": "Perfect! I've scheduled a haircut for you on April 11th at 2 PM. You'll receive a confirmation SMS shortly."},
        {"speaker": "customer", "text": "Thank you!"},
        {"speaker": "assistant", "text": "You're welcome! Is there anything else I can help you with?"},
        {"speaker": "customer", "text": "No, that's all. Thanks!"}
    ]
    
    result1 = await analyzer.analyze_conversation(
        conversation_history=conversation1,
        caller_phone="+1234567890",
        call_duration_seconds=120
    )
    
    print("\n📊 Analysis Results:")
    print(f"Appointments found: {len(result1.get('appointments', []))}")
    if result1.get('appointments'):
        for appt in result1['appointments']:
            print(f"  - {appt['customer_name']}: {appt['service_type']} on {appt['appointment_datetime']}")
    
    print(f"\nLeads found: {len(result1.get('leads', []))}")
    if result1.get('leads'):
        for lead in result1['leads']:
            print(f"  - {lead['name']}: Score {lead['lead_score']}/10")
    
    insights1 = result1.get('call_insights', {})
    print(f"\nCall Insights:")
    print(f"  Intent: {insights1.get('primary_intent')}")
    print(f"  Sentiment: {insights1.get('sentiment')}")
    print(f"  Resolution: {insights1.get('resolution_status')}")
    print(f"  Satisfaction: {insights1.get('customer_satisfaction')}")
    
    # Test 2: Sales inquiry conversation
    print("\n\nTest 2: Sales Inquiry Conversation")
    print("-"*60)
    
    conversation2 = [
        {"speaker": "assistant", "text": "Thank you for calling. How can I help you today?"},
        {"speaker": "customer", "text": "Hi, I'm interested in your premium spa package"},
        {"speaker": "assistant", "text": "Great! Our premium spa package includes massage, facial, and body treatment. It's $299. May I have your name?"},
        {"speaker": "customer", "text": "I'm Sarah Johnson"},
        {"speaker": "assistant", "text": "Thank you Sarah. Would you like to book this package or would you like more information?"},
        {"speaker": "customer", "text": "I need to think about it. Can someone call me back with more details?"},
        {"speaker": "assistant", "text": "Absolutely! Our team will call you back within 24 hours to discuss the premium package. What's the best number to reach you?"},
        {"speaker": "customer", "text": "You can reach me at this number"},
        {"speaker": "assistant", "text": "Perfect! We have your number. Our team will call you back soon. Is there anything else?"},
        {"speaker": "customer", "text": "No, that's all. Thank you!"}
    ]
    
    result2 = await analyzer.analyze_conversation(
        conversation_history=conversation2,
        caller_phone="+1987654321",
        call_duration_seconds=180
    )
    
    print("\n📊 Analysis Results:")
    print(f"Appointments found: {len(result2.get('appointments', []))}")
    print(f"Leads found: {len(result2.get('leads', []))}")
    if result2.get('leads'):
        for lead in result2['leads']:
            print(f"  - {lead['name']}: {lead['inquiry_details']}")
            print(f"    Score: {lead['lead_score']}/10, Timeline: {lead.get('timeline')}")
    
    insights2 = result2.get('call_insights', {})
    print(f"\nCall Insights:")
    print(f"  Intent: {insights2.get('primary_intent')}")
    print(f"  Sentiment: {insights2.get('sentiment')}")
    print(f"  Topics: {', '.join(insights2.get('key_topics', []))}")
    
    # Test 3: Support request
    print("\n\nTest 3: Support Request Conversation")
    print("-"*60)
    
    conversation3 = [
        {"speaker": "assistant", "text": "Thank you for calling. How can I help you today?"},
        {"speaker": "customer", "text": "I have a question about my recent appointment"},
        {"speaker": "assistant", "text": "I'd be happy to help. What's your question?"},
        {"speaker": "customer", "text": "I was charged twice for my last visit"},
        {"speaker": "assistant", "text": "I apologize for that inconvenience. Let me connect you with our billing team who can resolve this immediately."},
        {"speaker": "customer", "text": "Okay, thank you"}
    ]
    
    result3 = await analyzer.analyze_conversation(
        conversation_history=conversation3,
        caller_phone="+1555555555",
        call_duration_seconds=60
    )
    
    print("\n📊 Analysis Results:")
    insights3 = result3.get('call_insights', {})
    print(f"  Intent: {insights3.get('primary_intent')}")
    print(f"  Sentiment: {insights3.get('sentiment')}")
    print(f"  Resolution: {insights3.get('resolution_status')}")
    print(f"  Action Items: {', '.join(insights3.get('action_items', []))}")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_analyzer())
