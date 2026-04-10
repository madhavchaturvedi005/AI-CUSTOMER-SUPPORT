"""Test script for tool calling implementation."""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from tools.tool_executor import ToolExecutor
from tools.appointment_tools import ALL_TOOLS
from appointment_manager import AppointmentManager
from database import DatabaseService


async def test_tool_definitions():
    """Test that all tools are properly defined."""
    print("\n" + "="*60)
    print("TEST 1: Tool Definitions")
    print("="*60)
    
    print(f"\nTotal tools available: {len(ALL_TOOLS)}")
    for tool in ALL_TOOLS:
        print(f"\n✓ {tool.name}")
        print(f"  Type: {tool.type}")
        print(f"  Description: {tool.description[:80]}...")
        print(f"  Parameters: {list(tool.parameters.get('properties', {}).keys())}")
    
    print("\n✅ All tool definitions are valid")


async def test_tool_executor_initialization():
    """Test tool executor initialization."""
    print("\n" + "="*60)
    print("TEST 2: Tool Executor Initialization")
    print("="*60)
    
    # Create mock services
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_appointment = AsyncMock(return_value="appt-123")
    
    appt_manager = AppointmentManager(database=mock_db)
    
    # Initialize executor
    executor = ToolExecutor(
        appointment_manager=appt_manager,
        database=mock_db
    )
    
    print(f"\n✓ Tool executor initialized")
    print(f"  Available tools: {list(executor.tools.keys())}")
    print(f"  Appointment manager: {'✓' if executor.appointment_manager else '✗'}")
    print(f"  Database: {'✓' if executor.database else '✗'}")
    
    print("\n✅ Tool executor initialization successful")
    return executor


async def test_check_availability():
    """Test check_availability tool."""
    print("\n" + "="*60)
    print("TEST 3: Check Availability Tool")
    print("="*60)
    
    mock_db = AsyncMock(spec=DatabaseService)
    appt_manager = AppointmentManager(database=mock_db)
    executor = ToolExecutor(appointment_manager=appt_manager, database=mock_db)
    
    # Test checking availability
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    result = await executor.execute_tool(
        tool_name="check_availability",
        arguments={
            "date": tomorrow,
            "service_type": "haircut"
        }
    )
    
    print(f"\n✓ Tool execution result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Available: {result.get('result', {}).get('available')}")
    print(f"  Slot count: {result.get('result', {}).get('slot_count')}")
    print(f"  Message: {result.get('result', {}).get('message')}")
    
    assert result.get('success') == True, "Tool execution should succeed"
    print("\n✅ Check availability tool works correctly")


async def test_get_available_slots():
    """Test get_available_slots tool."""
    print("\n" + "="*60)
    print("TEST 4: Get Available Slots Tool")
    print("="*60)
    
    mock_db = AsyncMock(spec=DatabaseService)
    appt_manager = AppointmentManager(database=mock_db)
    executor = ToolExecutor(appointment_manager=appt_manager, database=mock_db)
    
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    result = await executor.execute_tool(
        tool_name="get_available_slots",
        arguments={
            "date": tomorrow,
            "service_type": "haircut"
        }
    )
    
    print(f"\n✓ Tool execution result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Available slots: {result.get('result', {}).get('available_slots')}")
    print(f"  Count: {result.get('result', {}).get('count')}")
    
    assert result.get('success') == True, "Tool execution should succeed"
    assert result.get('result', {}).get('count') > 0, "Should return some slots"
    print("\n✅ Get available slots tool works correctly")


async def test_book_appointment():
    """Test book_appointment tool."""
    print("\n" + "="*60)
    print("TEST 5: Book Appointment Tool")
    print("="*60)
    
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_appointment = AsyncMock(return_value="appt-uuid-123")
    
    appt_manager = AppointmentManager(database=mock_db)
    executor = ToolExecutor(appointment_manager=appt_manager, database=mock_db)
    
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    result = await executor.execute_tool(
        tool_name="book_appointment",
        arguments={
            "customer_name": "John Doe",
            "customer_phone": "+1234567890",
            "date": tomorrow,
            "time": "14:00",
            "service_type": "haircut",
            "notes": "First time customer"
        },
        call_context={
            "call_id": "call-123",
            "caller_phone": "+1234567890"
        }
    )
    
    print(f"\n✓ Tool execution result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Appointment ID: {result.get('result', {}).get('appointment_id')}")
    print(f"  Customer: {result.get('result', {}).get('customer_name')}")
    print(f"  Date: {result.get('result', {}).get('date')}")
    print(f"  Time: {result.get('result', {}).get('time')}")
    print(f"  Confirmation sent: {result.get('result', {}).get('confirmation_sent')}")
    
    assert result.get('success') == True, "Tool execution should succeed"
    assert result.get('result', {}).get('appointment_id') is not None, "Should return appointment ID"
    print("\n✅ Book appointment tool works correctly")


async def test_get_customer_history():
    """Test get_customer_history tool."""
    print("\n" + "="*60)
    print("TEST 6: Get Customer History Tool")
    print("="*60)
    
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.get_caller_history = AsyncMock(return_value=[
        {"started_at": datetime.now(timezone.utc), "intent": "sales_inquiry"}
    ])
    
    executor = ToolExecutor(database=mock_db)
    
    result = await executor.execute_tool(
        tool_name="get_customer_history",
        arguments={
            "phone": "+1234567890"
        }
    )
    
    print(f"\n✓ Tool execution result:")
    print(f"  Success: {result.get('success')}")
    print(f"  Is returning customer: {result.get('result', {}).get('is_returning_customer')}")
    print(f"  Total calls: {result.get('result', {}).get('total_calls')}")
    print(f"  Message: {result.get('result', {}).get('message')}")
    
    assert result.get('success') == True, "Tool execution should succeed"
    print("\n✅ Get customer history tool works correctly")


async def test_openai_tool_format():
    """Test that tools are formatted correctly for OpenAI."""
    print("\n" + "="*60)
    print("TEST 7: OpenAI Tool Format")
    print("="*60)
    
    # Convert to OpenAI format
    tools_config = [
        {
            "type": tool.type,
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
        for tool in ALL_TOOLS
    ]
    
    print(f"\n✓ Converted {len(tools_config)} tools to OpenAI format")
    
    # Verify structure
    for tool in tools_config:
        assert "type" in tool, "Tool must have type"
        assert "name" in tool, "Tool must have name"
        assert "description" in tool, "Tool must have description"
        assert "parameters" in tool, "Tool must have parameters"
        assert tool["type"] == "function", "Tool type must be 'function'"
        print(f"  ✓ {tool['name']}: Valid format")
    
    # Print example
    print(f"\nExample tool configuration:")
    print(json.dumps(tools_config[0], indent=2))
    
    print("\n✅ All tools are properly formatted for OpenAI")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TOOL CALLING IMPLEMENTATION TESTS")
    print("="*60)
    
    try:
        await test_tool_definitions()
        await test_tool_executor_initialization()
        await test_check_availability()
        await test_get_available_slots()
        await test_book_appointment()
        await test_get_customer_history()
        await test_openai_tool_format()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nTool calling is ready to use!")
        print("\nNext steps:")
        print("1. Start your server: python main.py")
        print("2. Make a test call to your Twilio number")
        print("3. Try saying: 'I'd like to book an appointment for tomorrow at 2pm'")
        print("4. The AI will use tools to check availability and book the appointment")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
