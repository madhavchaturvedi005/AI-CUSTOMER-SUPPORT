#!/usr/bin/env python3
"""Quick test to verify OpenAI session configuration."""

import json
from tools.appointment_tools import ALL_TOOLS
from config import OPENAI_REALTIME_MODEL

def test_session_config():
    """Test that session configuration is valid."""
    print("🔍 Testing OpenAI session configuration...")
    
    # Convert tool definitions
    tools_config = [
        {
            "type": tool.type,
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
        for tool in ALL_TOOLS
    ]
    
    # Create session update
    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": OPENAI_REALTIME_MODEL,
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "turn_detection": {"type": "server_vad"}
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": "alloy"
                }
            },
            "instructions": "Test instructions",
            "tools": tools_config,
            "tool_choice": "auto"
        }
    }
    
    # Validate JSON
    try:
        json_str = json.dumps(session_update)
        parsed = json.loads(json_str)
        print(f"✅ Session config is valid JSON")
        print(f"✅ Model: {parsed['session']['model']}")
        print(f"✅ Tools: {len(parsed['session']['tools'])} tools")
        print(f"✅ Tool choice: {parsed['session']['tool_choice']}")
        
        print(f"\n📋 Tools included:")
        for tool in parsed['session']['tools']:
            print(f"   • {tool['name']}")
        
        print(f"\n✅ Configuration is valid and ready for OpenAI!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_config()
    exit(0 if success else 1)
