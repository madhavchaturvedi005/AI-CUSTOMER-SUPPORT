"""Example demonstrating the clarification request logic for low-confidence intents.

This example shows how the CallManager integrates with IntentDetector to:
1. Detect intent with confidence scoring
2. Request clarification when confidence < 0.7
3. Update intent after receiving clarification response

**Validates: Requirement 3.4**
"""

import asyncio
from call_manager import CallManager
from intent_detector import OpenAIIntentDetector
from models import Intent, Language
from database import DatabaseService
from redis_service import RedisService


async def demonstrate_clarification_flow():
    """Demonstrate the complete clarification flow."""
    
    # Initialize services (in production, these would be real instances)
    # For this example, we'll use mock implementations
    print("=== Clarification Request Logic Demo ===\n")
    
    # Scenario 1: High confidence - no clarification needed
    print("Scenario 1: High Confidence Intent Detection")
    print("-" * 50)
    print("Caller: 'I want to buy your premium subscription'")
    print("Detected Intent: SALES_INQUIRY")
    print("Confidence: 0.85")
    print("Action: No clarification needed, proceed with sales flow")
    print()
    
    # Scenario 2: Low confidence - clarification requested
    print("Scenario 2: Low Confidence Intent Detection")
    print("-" * 50)
    print("Caller: 'Hello, I need something'")
    print("Detected Intent: UNKNOWN")
    print("Confidence: 0.50")
    print("Action: Request clarification")
    print("AI Response: 'I want to make sure I can help you properly. Could you tell me a bit more about what you're looking for?'")
    print()
    
    # Scenario 3: After clarification
    print("Scenario 3: Intent Update After Clarification")
    print("-" * 50)
    print("Caller: 'I need help with my account login'")
    print("Re-detected Intent: SUPPORT_REQUEST")
    print("Confidence: 0.88")
    print("Action: Proceed with support flow")
    print()
    
    # Scenario 4: Threshold boundary (exactly 0.7)
    print("Scenario 4: Threshold Boundary (0.7)")
    print("-" * 50)
    print("Caller: 'I'm interested in your services'")
    print("Detected Intent: SALES_INQUIRY")
    print("Confidence: 0.70")
    print("Action: No clarification needed (>= 0.7 threshold)")
    print()
    
    # Scenario 5: Multiple intent types with low confidence
    print("Scenario 5: Different Intent Types with Low Confidence")
    print("-" * 50)
    
    intent_examples = {
        Intent.SALES_INQUIRY: "I want to make sure I understand correctly - are you interested in learning more about our products or services?",
        Intent.SUPPORT_REQUEST: "Just to clarify, are you looking for technical support or assistance with an existing product?",
        Intent.APPOINTMENT_BOOKING: "Would you like to schedule an appointment with us?",
        Intent.COMPLAINT: "I understand you may have a concern. Could you tell me more about the issue you're experiencing?",
        Intent.GENERAL_INQUIRY: "How can I best assist you today? Are you looking for information about our services?"
    }
    
    for intent, clarification in intent_examples.items():
        print(f"\nIntent: {intent.value}")
        print(f"Clarification: {clarification}")
    
    print("\n" + "=" * 50)
    print("Key Features:")
    print("- Threshold: confidence < 0.7 triggers clarification")
    print("- Contextual questions based on detected intent")
    print("- Intent re-detection after clarification response")
    print("- Metadata tracking for clarification state")
    print("=" * 50)


async def demonstrate_api_usage():
    """Show how to use the clarification API in code."""
    
    print("\n\n=== API Usage Example ===\n")
    
    code_example = '''
# Step 1: Detect intent with clarification check
intent, confidence, clarification = await call_manager.handle_intent_with_clarification(
    call_sid="CA1234567890",
    intent_detector=intent_detector,
    conversation_history=[
        {"speaker": "assistant", "text": "Hello, how can I help?", "timestamp": 0}
    ],
    current_transcript="I need something"
)

# Step 2: Check if clarification is needed
if clarification:
    # Low confidence detected - ask clarification question
    print(f"AI: {clarification}")
    
    # Wait for caller response...
    caller_response = "I need help with my account"
    
    # Step 3: Update intent after clarification
    updated_intent, updated_confidence = await call_manager.update_intent_after_clarification(
        call_sid="CA1234567890",
        intent_detector=intent_detector,
        clarification_response=caller_response
    )
    
    print(f"Updated Intent: {updated_intent.value}")
    print(f"Updated Confidence: {updated_confidence}")
else:
    # High confidence - proceed directly
    print(f"Intent: {intent.value} (confidence: {confidence})")
    # Route call based on intent...
'''
    
    print(code_example)


if __name__ == "__main__":
    asyncio.run(demonstrate_clarification_flow())
    asyncio.run(demonstrate_api_usage())
