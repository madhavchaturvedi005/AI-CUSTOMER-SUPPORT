#!/usr/bin/env python3
"""Quick verification script for tool calling setup."""

import sys

def verify_imports():
    """Verify all required modules can be imported."""
    print("🔍 Verifying imports...")
    
    try:
        from tools.tool_executor import ToolExecutor
        print("  ✅ ToolExecutor")
    except ImportError as e:
        print(f"  ❌ ToolExecutor: {e}")
        return False
    
    try:
        from tools.appointment_tools import ALL_TOOLS
        print(f"  ✅ Tool definitions ({len(ALL_TOOLS)} tools)")
    except ImportError as e:
        print(f"  ❌ Tool definitions: {e}")
        return False
    
    try:
        import handlers
        print("  ✅ handlers.py (with tool call handler)")
    except ImportError as e:
        print(f"  ❌ handlers.py: {e}")
        return False
    
    try:
        from session import SessionState
        state = SessionState()
        if hasattr(state, 'initialize_tool_executor'):
            print("  ✅ SessionState (with tool executor support)")
        else:
            print("  ⚠️  SessionState missing initialize_tool_executor")
            return False
    except ImportError as e:
        print(f"  ❌ SessionState: {e}")
        return False
    
    return True


def verify_tool_definitions():
    """Verify tool definitions are valid."""
    print("\n🔍 Verifying tool definitions...")
    
    from tools.appointment_tools import ALL_TOOLS
    
    required_fields = ['type', 'name', 'description', 'parameters']
    
    for tool in ALL_TOOLS:
        tool_dict = tool.dict()
        missing = [f for f in required_fields if f not in tool_dict]
        if missing:
            print(f"  ❌ {tool.name}: Missing fields {missing}")
            return False
        print(f"  ✅ {tool.name}")
    
    return True


def verify_tool_executor():
    """Verify tool executor can be initialized."""
    print("\n🔍 Verifying tool executor...")
    
    from tools.tool_executor import ToolExecutor
    from unittest.mock import AsyncMock
    
    try:
        executor = ToolExecutor(
            appointment_manager=AsyncMock(),
            database=AsyncMock()
        )
        
        expected_tools = [
            'check_availability',
            'get_available_slots',
            'book_appointment',
            'create_lead',
            'get_customer_history',
            'send_sms'
        ]
        
        for tool_name in expected_tools:
            if tool_name in executor.tools:
                print(f"  ✅ {tool_name}")
            else:
                print(f"  ❌ {tool_name} not registered")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def verify_openai_format():
    """Verify tools can be formatted for OpenAI."""
    print("\n🔍 Verifying OpenAI format...")
    
    from tools.appointment_tools import ALL_TOOLS
    
    try:
        tools_config = [
            {
                "type": tool.type,
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in ALL_TOOLS
        ]
        
        print(f"  ✅ Converted {len(tools_config)} tools to OpenAI format")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("="*60)
    print("TOOL CALLING VERIFICATION")
    print("="*60)
    
    checks = [
        ("Imports", verify_imports),
        ("Tool Definitions", verify_tool_definitions),
        ("Tool Executor", verify_tool_executor),
        ("OpenAI Format", verify_openai_format)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\nTool calling is ready to use!")
        print("\nTo start the server:")
        print("  python3 main.py")
        print("\nTo run full tests:")
        print("  python3 test_tool_calling.py")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ SOME CHECKS FAILED")
        print("="*60)
        print("\nPlease fix the issues above before using tool calling.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
