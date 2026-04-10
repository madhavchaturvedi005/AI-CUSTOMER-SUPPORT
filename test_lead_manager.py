"""Tests for LeadManager service."""

import pytest
from unittest.mock import AsyncMock
from lead_manager import LeadManager
from models import LeadData
from database import DatabaseService


@pytest.mark.asyncio
async def test_collect_lead_info_success():
    """Test successful lead information collection."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    conversation_history = [
        {"speaker": "assistant", "text": "What's your name?"},
        {"speaker": "caller", "text": "My name is John Smith"},
        {"speaker": "assistant", "text": "What can I help you with?"},
        {"speaker": "caller", "text": "I want to buy your premium product. My email is john@example.com"}
    ]
    
    # Execute
    lead = await lead_manager.collect_lead_info(
        call_id="call-123",
        conversation_history=conversation_history,
        caller_phone="+1234567890"
    )
    
    # Verify
    assert lead is not None
    assert lead.name == "John Smith"
    assert lead.phone == "+1234567890"
    assert lead.email == "john@example.com"
    assert "premium product" in lead.inquiry_details
    
    print("✅ Test passed: Lead information collected successfully")


@pytest.mark.asyncio
async def test_collect_lead_info_insufficient_data():
    """Test lead collection with insufficient data."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    conversation_history = [
        {"speaker": "assistant", "text": "Hello"},
        {"speaker": "caller", "text": "Hi"}  # No name or inquiry
    ]
    
    # Execute
    lead = await lead_manager.collect_lead_info(
        call_id="call-456",
        conversation_history=conversation_history,
        caller_phone="+9876543210"
    )
    
    # Verify
    assert lead is None
    
    print("✅ Test passed: Returns None for insufficient data")


@pytest.mark.asyncio
async def test_qualify_lead():
    """Test lead qualification."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    lead = LeadData(
        name="Jane Doe",
        phone="+1234567890",
        inquiry_details="Product inquiry"
    )
    
    conversation_history = [
        {"speaker": "caller", "text": "I have a high budget for this"},
        {"speaker": "caller", "text": "I need it immediately"},
        {"speaker": "caller", "text": "I'm the owner so I can decide"}
    ]
    
    # Execute
    qualified_lead = await lead_manager.qualify_lead(lead, conversation_history)
    
    # Verify
    assert qualified_lead.budget_indication == "high"
    assert qualified_lead.timeline == "immediate"
    assert qualified_lead.decision_authority is True
    
    print("✅ Test passed: Lead qualified successfully")


@pytest.mark.asyncio
async def test_score_lead_high_value():
    """Test lead scoring for high-value lead."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    lead = LeadData(
        name="High Value Lead",
        phone="+1234567890",
        email="high@example.com",
        inquiry_details="Enterprise solution",
        budget_indication="high",
        timeline="immediate",
        decision_authority=True
    )
    
    # Execute
    score = await lead_manager.score_lead(lead)
    
    # Verify
    assert score >= 7  # High-value threshold
    assert score <= 10
    assert lead.lead_score == score
    
    print(f"✅ Test passed: High-value lead scored {score}/10")


@pytest.mark.asyncio
async def test_score_lead_low_value():
    """Test lead scoring for low-value lead."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    lead = LeadData(
        name="Low Value Lead",
        phone="+1234567890",
        inquiry_details="Just browsing"
    )
    
    # Execute
    score = await lead_manager.score_lead(lead)
    
    # Verify
    assert score < 7  # Below high-value threshold
    assert score >= 1
    assert lead.lead_score == score
    
    print(f"✅ Test passed: Low-value lead scored {score}/10")


@pytest.mark.asyncio
async def test_score_lead_boundaries():
    """Test lead scoring stays within 1-10 boundaries."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    # Maximum score scenario
    max_lead = LeadData(
        name="Max Lead",
        phone="+1234567890",
        email="max@example.com",
        inquiry_details="Urgent enterprise deal",
        budget_indication="high budget unlimited",
        timeline="immediate urgent asap",
        decision_authority=True
    )
    
    max_score = await lead_manager.score_lead(max_lead)
    assert max_score <= 10
    
    # Minimum score scenario
    min_lead = LeadData(
        name="Min Lead",
        phone="+1234567890",
        inquiry_details="Maybe later"
    )
    
    min_score = await lead_manager.score_lead(min_lead)
    assert min_score >= 1
    
    print(f"✅ Test passed: Scores within boundaries (min={min_score}, max={max_score})")


@pytest.mark.asyncio
async def test_is_high_value_lead():
    """Test high-value lead identification."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    # High-value lead
    high_lead = LeadData(
        name="High Lead",
        phone="+1234567890",
        inquiry_details="Test",
        lead_score=8
    )
    
    assert lead_manager.is_high_value_lead(high_lead) is True
    
    # Low-value lead
    low_lead = LeadData(
        name="Low Lead",
        phone="+1234567890",
        inquiry_details="Test",
        lead_score=5
    )
    
    assert lead_manager.is_high_value_lead(low_lead) is False
    
    # Boundary case (score = 7)
    boundary_lead = LeadData(
        name="Boundary Lead",
        phone="+1234567890",
        inquiry_details="Test",
        lead_score=7
    )
    
    assert lead_manager.is_high_value_lead(boundary_lead) is True
    
    print("✅ Test passed: High-value lead identification works correctly")


@pytest.mark.asyncio
async def test_save_lead():
    """Test saving lead to database."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_lead = AsyncMock(return_value="lead-uuid-123")
    lead_manager = LeadManager(database=mock_db)
    
    lead = LeadData(
        name="Test Lead",
        phone="+1234567890",
        email="test@example.com",
        inquiry_details="Product inquiry",
        budget_indication="medium",
        timeline="short-term",
        decision_authority=True,
        lead_score=7
    )
    
    # Execute
    lead_id = await lead_manager.save_lead("call-123", lead)
    
    # Verify
    assert lead_id == "lead-uuid-123"
    assert mock_db.create_lead.called
    
    # Verify correct parameters passed
    call_args = mock_db.create_lead.call_args
    assert call_args.kwargs["call_id"] == "call-123"
    assert call_args.kwargs["name"] == "Test Lead"
    assert call_args.kwargs["phone"] == "+1234567890"
    assert call_args.kwargs["email"] == "test@example.com"
    assert call_args.kwargs["lead_score"] == 7
    
    print("✅ Test passed: Lead saved to database")


@pytest.mark.asyncio
async def test_process_lead_complete_pipeline():
    """Test complete lead processing pipeline."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_lead = AsyncMock(return_value="lead-uuid-456")
    lead_manager = LeadManager(database=mock_db)
    
    conversation_history = [
        {"speaker": "caller", "text": "Hi, my name is Alice Johnson"},
        {"speaker": "assistant", "text": "How can I help you?"},
        {"speaker": "caller", "text": "I want to buy your enterprise solution. I have a high budget and need it immediately."},
        {"speaker": "caller", "text": "I'm the CEO so I can make the decision. My email is alice@company.com"}
    ]
    
    # Execute
    lead, is_high_value = await lead_manager.process_lead(
        call_id="call-789",
        conversation_history=conversation_history,
        caller_phone="+1234567890"
    )
    
    # Verify
    assert lead is not None
    assert lead.name == "Alice Johnson"
    assert lead.email == "alice@company.com"
    assert lead.budget_indication == "high"
    assert lead.timeline == "immediate"
    assert lead.decision_authority is True
    assert lead.lead_score >= 7
    assert is_high_value is True
    assert mock_db.create_lead.called
    
    print(f"✅ Test passed: Complete pipeline processed high-value lead (score={lead.lead_score})")


@pytest.mark.asyncio
async def test_extract_name_patterns():
    """Test various name extraction patterns."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    # Test "my name is" pattern
    history1 = [{"speaker": "caller", "text": "Hello, my name is Bob Wilson"}]
    name1 = lead_manager._extract_name(history1)
    assert name1 == "Bob Wilson"
    
    # Test "I'm" pattern
    history2 = [{"speaker": "caller", "text": "Hi, I'm Sarah Davis"}]
    name2 = lead_manager._extract_name(history2)
    assert name2 == "Sarah Davis"
    
    # Test "this is" pattern
    history3 = [{"speaker": "caller", "text": "Hello, this is Mike Brown"}]
    name3 = lead_manager._extract_name(history3)
    assert name3 == "Mike Brown"
    
    print("✅ Test passed: Name extraction patterns work correctly")


@pytest.mark.asyncio
async def test_extract_name_patterns():
    """Test various name extraction patterns."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    lead_manager = LeadManager(database=mock_db)
    
    # Test "my name is" pattern
    history1 = [{"speaker": "caller", "text": "Hello, my name is Bob Wilson"}]
    name1 = lead_manager._extract_name(history1)
    assert name1 == "Bob Wilson"
    
    # Test "I'm" pattern
    history2 = [{"speaker": "caller", "text": "Hi, I'm Sarah Davis"}]
    name2 = lead_manager._extract_name(history2)
    assert name2 == "Sarah Davis"
    
    # Test "this is" pattern
    history3 = [{"speaker": "caller", "text": "Hello, this is Mike Brown"}]
    name3 = lead_manager._extract_name(history3)
    assert name3 == "Mike Brown"
    
    print("✅ Test passed: Name extraction patterns work correctly")


@pytest.mark.asyncio
async def test_trigger_high_value_notification():
    """Test high-value lead notification triggering."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    notification_triggered = []
    
    def notification_callback(lead: LeadData):
        notification_triggered.append(lead)
    
    lead_manager = LeadManager(
        database=mock_db,
        notification_callback=notification_callback
    )
    
    # High-value lead
    high_lead = LeadData(
        name="VIP Lead",
        phone="+1234567890",
        email="vip@example.com",
        inquiry_details="Enterprise deal",
        lead_score=9
    )
    
    # Execute
    await lead_manager.trigger_high_value_notification(high_lead)
    
    # Verify
    assert len(notification_triggered) == 1
    assert notification_triggered[0].name == "VIP Lead"
    assert notification_triggered[0].lead_score == 9
    
    print("✅ Test passed: High-value lead notification triggered")


@pytest.mark.asyncio
async def test_no_notification_for_low_value_lead():
    """Test that low-value leads don't trigger notifications."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    notification_triggered = []
    
    def notification_callback(lead: LeadData):
        notification_triggered.append(lead)
    
    lead_manager = LeadManager(
        database=mock_db,
        notification_callback=notification_callback
    )
    
    # Low-value lead
    low_lead = LeadData(
        name="Low Lead",
        phone="+1234567890",
        inquiry_details="Just browsing",
        lead_score=4
    )
    
    # Execute
    await lead_manager.trigger_high_value_notification(low_lead)
    
    # Verify
    assert len(notification_triggered) == 0
    
    print("✅ Test passed: No notification for low-value lead")


@pytest.mark.asyncio
async def test_process_lead_triggers_notification():
    """Test that process_lead triggers notification for high-value leads."""
    # Setup
    mock_db = AsyncMock(spec=DatabaseService)
    mock_db.create_lead = AsyncMock(return_value="lead-uuid-999")
    notification_triggered = []
    
    async def async_notification_callback(lead: LeadData):
        notification_triggered.append(lead)
    
    lead_manager = LeadManager(
        database=mock_db,
        notification_callback=async_notification_callback
    )
    
    conversation_history = [
        {"speaker": "caller", "text": "Hi, my name is Premium Customer"},
        {"speaker": "caller", "text": "I want to buy your enterprise solution with a high budget immediately."},
        {"speaker": "caller", "text": "I'm the CEO so I can make the decision. Email: premium@company.com"}
    ]
    
    # Execute
    lead, is_high_value = await lead_manager.process_lead(
        call_id="call-999",
        conversation_history=conversation_history,
        caller_phone="+1234567890"
    )
    
    # Verify
    assert is_high_value is True
    assert len(notification_triggered) == 1
    assert notification_triggered[0].name == "Premium Customer"
    
    print("✅ Test passed: process_lead triggers notification for high-value lead")


if __name__ == "__main__":
    import asyncio
    
    print("\n🧪 Running Lead Manager Tests...\n")
    
    asyncio.run(test_collect_lead_info_success())
    asyncio.run(test_collect_lead_info_insufficient_data())
    asyncio.run(test_qualify_lead())
    asyncio.run(test_score_lead_high_value())
    asyncio.run(test_score_lead_low_value())
    asyncio.run(test_score_lead_boundaries())
    asyncio.run(test_is_high_value_lead())
    asyncio.run(test_save_lead())
    asyncio.run(test_process_lead_complete_pipeline())
    asyncio.run(test_extract_name_patterns())
    asyncio.run(test_trigger_high_value_notification())
    asyncio.run(test_no_notification_for_low_value_lead())
    asyncio.run(test_process_lead_triggers_notification())
    
    print("\n✅ All Lead Manager tests passed!")
    print("\nRequirements validated:")
    print("  • 5.1: Collect caller name, contact number, and inquiry details ✓")
    print("  • 5.2: Qualify leads based on budget, timeline, and decision authority ✓")
    print("  • 5.3: Assign lead score from 1 to 10 ✓")
    print("  • 5.4: Store lead information in structured format ✓")
    print("  • 5.5: Trigger immediate notification for high-value leads ✓")
