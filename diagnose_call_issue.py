#!/usr/bin/env python3
"""Diagnostic script for OpenAI response issues."""

import os
from dotenv import load_dotenv

load_dotenv()

def check_environment():
    """Check environment variables."""
    print("="*60)
    print("1. ENVIRONMENT VARIABLES")
    print("="*60)
    
    checks = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OPENAI_REALTIME_MODEL": os.getenv("OPENAI_REALTIME_MODEL"),
        "PORT": os.getenv("PORT"),
        "BUSINESS_NAME": os.getenv("BUSINESS_NAME"),
    }
    
    all_good = True
    for key, value in checks.items():
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {key}: {masked}")
        else:
            print(f"❌ {key}: NOT SET")
            all_good = False
    
    return all_good


def check_imports():
    """Check if all modules import correctly."""
    print("\n" + "="*60)
    print("2. MODULE IMPORTS")
    print("="*60)
    
    modules = [
        ("tools.tool_executor", "ToolExecutor"),
        ("tools.appointment_tools", "ALL_TOOLS"),
        ("handlers", "handle_tool_call"),
        ("session", "SessionState"),
        ("main", "app"),
    ]
    
    all_good = True
    for module_name, item_name in modules:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"✅ {module_name}.{item_name}")
        except Exception as e:
            print(f"❌ {module_name}.{item_name}: {e}")
            all_good = False
    
    return all_good


def check_tool_configuration():
    """Check tool configuration."""
    print("\n" + "="*60)
    print("3. TOOL CONFIGURATION")
    print("="*60)
    
    try:
        from tools.appointment_tools import ALL_TOOLS
        print(f"✅ {len(ALL_TOOLS)} tools defined")
        
        for tool in ALL_TOOLS:
            print(f"   • {tool.name}")
        
        # Check if tools can be converted to OpenAI format
        tools_config = [
            {
                "type": tool.type,
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in ALL_TOOLS
        ]
        
        print(f"✅ Tools can be converted to OpenAI format")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_session_initialization():
    """Check session initialization."""
    print("\n" + "="*60)
    print("4. SESSION INITIALIZATION")
    print("="*60)
    
    try:
        from session import SessionState
        from unittest.mock import AsyncMock
        
        state = SessionState()
        
        # Check if tool executor can be initialized
        if hasattr(state, 'initialize_tool_executor'):
            print("✅ SessionState has initialize_tool_executor method")
            
            # Try to initialize
            state.initialize_tool_executor(
                appointment_manager=AsyncMock(),
                database=AsyncMock()
            )
            
            if state.tool_executor:
                print("✅ Tool executor initialized successfully")
                print(f"   Available tools: {len(state.tool_executor.tools)}")
                return True
            else:
                print("❌ Tool executor is None after initialization")
                return False
        else:
            print("❌ SessionState missing initialize_tool_executor method")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_openai_config():
    """Check OpenAI configuration."""
    print("\n" + "="*60)
    print("5. OPENAI CONFIGURATION")
    print("="*60)
    
    try:
        from config import OPENAI_REALTIME_MODEL, SYSTEM_MESSAGE
        
        print(f"✅ Model: {OPENAI_REALTIME_MODEL}")
        print(f"✅ System message length: {len(SYSTEM_MESSAGE)} characters")
        
        if len(SYSTEM_MESSAGE) > 10000:
            print(f"⚠️  Warning: System message is very long ({len(SYSTEM_MESSAGE)} chars)")
            print(f"   This might cause issues with OpenAI")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_handlers():
    """Check handlers configuration."""
    print("\n" + "="*60)
    print("6. HANDLERS")
    print("="*60)
    
    try:
        import handlers
        
        # Check if handle_tool_call exists
        if hasattr(handlers, 'handle_tool_call'):
            print("✅ handle_tool_call function exists")
        else:
            print("❌ handle_tool_call function not found")
            return False
        
        # Check if Dict is imported
        import inspect
        source = inspect.getsource(handlers.handle_tool_call)
        if 'Dict[str, Any]' in source or 'Dict' in source:
            print("✅ Type hints are properly imported")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic checks."""
    print("\n" + "="*60)
    print("OPENAI RESPONSE DIAGNOSTIC")
    print("="*60)
    print("\nThis script checks if tool calling is properly configured")
    print("and identifies any issues preventing OpenAI from responding.\n")
    
    checks = [
        ("Environment Variables", check_environment),
        ("Module Imports", check_imports),
        ("Tool Configuration", check_tool_configuration),
        ("Session Initialization", check_session_initialization),
        ("OpenAI Configuration", check_openai_config),
        ("Handlers", check_handlers),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\nYour configuration looks good!")
        print("\nIf OpenAI still doesn't respond:")
        print("1. Check your OpenAI API key is valid")
        print("2. Verify your account has access to Realtime API")
        print("3. Check server logs for WebSocket errors")
        print("4. Make sure Twilio is sending audio to your server")
        print("\nStart server: python3 main.py")
        print("Then make a test call and check the logs.")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ SOME CHECKS FAILED")
        print("="*60)
        print("\nPlease fix the issues above before testing.")
        print("\nCommon fixes:")
        print("- Set missing environment variables in .env")
        print("- Run: pip install -r requirements.txt")
        print("- Check for syntax errors in modified files")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
