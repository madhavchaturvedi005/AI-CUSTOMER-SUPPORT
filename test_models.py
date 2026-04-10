"""Unit tests for core data models and enums."""

import pytest
from datetime import datetime, timedelta, timezone
from models import (
    CallStatus, Intent, Language,
    CallContext, LeadData, AppointmentData
)


class TestEnums:
    """Test enum definitions."""
    
    def test_call_status_values(self):
        """Test CallStatus enum has all expected values."""
        assert CallStatus.INITIATED.value == "initiated"
        assert CallStatus.RINGING.value == "ringing"
        assert CallStatus.IN_PROGRESS.value == "in_progress"
        assert CallStatus.COMPLETED.value == "completed"
        assert CallStatus.FAILED.value == "failed"
        assert CallStatus.NO_ANSWER.value == "no_answer"
    
    def test_intent_values(self):
        """Test Intent enum has all expected values."""
        assert Intent.SALES_INQUIRY.value == "sales_inquiry"
        assert Intent.SUPPORT_REQUEST.value == "support_request"
        assert Intent.APPOINTMENT_BOOKING.value == "appointment_booking"
        assert Intent.COMPLAINT.value == "complaint"
        assert Intent.GENERAL_INQUIRY.value == "general_inquiry"
        assert Intent.UNKNOWN.value == "unknown"
    
    def test_language_values(self):
        """Test Language enum has all expected values."""
        assert Language.ENGLISH.value == "en"
        assert Language.HINDI.value == "hi"
        assert Language.TAMIL.value == "ta"
        assert Language.TELUGU.value == "te"
        assert Language.BENGALI.value == "bn"


class TestCallContext:
    """Test CallContext dataclass."""
    
    def test_call_context_creation(self):
        """Test creating a valid CallContext."""
        context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890"
        )
        assert context.call_id == "test-123"
        assert context.caller_phone == "+1234567890"
        assert context.language == Language.ENGLISH
        assert context.intent is None
        assert context.intent_confidence == 0.0
        assert context.conversation_history == []
        assert context.lead_data is None
        assert context.appointment_data is None
        assert context.metadata == {}
        assert isinstance(context.created_at, datetime)
    
    def test_call_context_with_optional_fields(self):
        """Test CallContext with optional fields populated."""
        context = CallContext(
            call_id="test-456",
            caller_phone="+9876543210",
            caller_name="John Doe",
            language=Language.HINDI,
            intent=Intent.SALES_INQUIRY,
            intent_confidence=0.85,
            conversation_history=[{"role": "user", "content": "Hello"}],
            lead_data={"name": "John"},
            appointment_data={"time": "2pm"},
            metadata={"source": "mobile"}
        )
        assert context.caller_name == "John Doe"
        assert context.language == Language.HINDI
        assert context.intent == Intent.SALES_INQUIRY
        assert context.intent_confidence == 0.85
        assert len(context.conversation_history) == 1
        assert context.lead_data == {"name": "John"}
        assert context.appointment_data == {"time": "2pm"}
        assert context.metadata == {"source": "mobile"}
    
    def test_call_context_validation_empty_call_id(self):
        """Test validation fails for empty call_id."""
        context = CallContext(call_id="", caller_phone="+1234567890")
        with pytest.raises(ValueError, match="call_id cannot be empty"):
            context.validate()
    
    def test_call_context_validation_empty_caller_phone(self):
        """Test validation fails for empty caller_phone."""
        context = CallContext(call_id="test-123", caller_phone="")
        with pytest.raises(ValueError, match="caller_phone cannot be empty"):
            context.validate()
    
    def test_call_context_validation_invalid_confidence(self):
        """Test validation fails for invalid intent_confidence."""
        context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent_confidence=1.5
        )
        with pytest.raises(ValueError, match="intent_confidence must be between 0.0 and 1.0"):
            context.validate()
        
        context.intent_confidence = -0.1
        with pytest.raises(ValueError, match="intent_confidence must be between 0.0 and 1.0"):
            context.validate()
    
    def test_call_context_validation_valid(self):
        """Test validation passes for valid CallContext."""
        context = CallContext(
            call_id="test-123",
            caller_phone="+1234567890",
            intent=Intent.SALES_INQUIRY,
            intent_confidence=0.75
        )
        context.validate()  # Should not raise


class TestLeadData:
    """Test LeadData dataclass."""
    
    def test_lead_data_creation(self):
        """Test creating a valid LeadData."""
        lead = LeadData(
            name="Jane Smith",
            phone="+1234567890"
        )
        assert lead.name == "Jane Smith"
        assert lead.phone == "+1234567890"
        assert lead.email is None
        assert lead.inquiry_details == ""
        assert lead.budget_indication is None
        assert lead.timeline is None
        assert lead.decision_authority is False
        assert lead.lead_score == 0
        assert lead.source == "voice_call"
    
    def test_lead_data_with_optional_fields(self):
        """Test LeadData with optional fields populated."""
        lead = LeadData(
            name="Jane Smith",
            phone="+1234567890",
            email="jane@example.com",
            inquiry_details="Interested in product X",
            budget_indication="$10k-$20k",
            timeline="Q2 2024",
            decision_authority=True,
            lead_score=8,
            source="web_form"
        )
        assert lead.email == "jane@example.com"
        assert lead.inquiry_details == "Interested in product X"
        assert lead.budget_indication == "$10k-$20k"
        assert lead.timeline == "Q2 2024"
        assert lead.decision_authority is True
        assert lead.lead_score == 8
        assert lead.source == "web_form"
    
    def test_lead_data_validation_empty_name(self):
        """Test validation fails for empty name."""
        lead = LeadData(name="", phone="+1234567890")
        with pytest.raises(ValueError, match="name cannot be empty"):
            lead.validate()
    
    def test_lead_data_validation_empty_phone(self):
        """Test validation fails for empty phone."""
        lead = LeadData(name="Jane Smith", phone="")
        with pytest.raises(ValueError, match="phone cannot be empty"):
            lead.validate()
    
    def test_lead_data_validation_invalid_lead_score(self):
        """Test validation fails for invalid lead_score."""
        lead = LeadData(name="Jane Smith", phone="+1234567890", lead_score=11)
        with pytest.raises(ValueError, match="lead_score must be between 0 and 10"):
            lead.validate()
        
        lead.lead_score = -1
        with pytest.raises(ValueError, match="lead_score must be between 0 and 10"):
            lead.validate()
    
    def test_lead_data_validation_invalid_email(self):
        """Test validation fails for invalid email."""
        lead = LeadData(
            name="Jane Smith",
            phone="+1234567890",
            email="invalid-email"
        )
        with pytest.raises(ValueError, match="email must be a valid email address"):
            lead.validate()
    
    def test_lead_data_validation_valid(self):
        """Test validation passes for valid LeadData."""
        lead = LeadData(
            name="Jane Smith",
            phone="+1234567890",
            email="jane@example.com",
            lead_score=7
        )
        lead.validate()  # Should not raise


class TestAppointmentData:
    """Test AppointmentData dataclass."""
    
    def test_appointment_data_creation(self):
        """Test creating a valid AppointmentData."""
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890"
        )
        assert appointment.customer_name == "Bob Johnson"
        assert appointment.customer_phone == "+1234567890"
        assert appointment.customer_email is None
        assert appointment.service_type == ""
        assert appointment.appointment_datetime is None
        assert appointment.duration_minutes == 30
        assert appointment.notes is None
        assert appointment.confirmation_sent is False
    
    def test_appointment_data_with_optional_fields(self):
        """Test AppointmentData with optional fields populated."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890",
            customer_email="bob@example.com",
            service_type="Consultation",
            appointment_datetime=future_time,
            duration_minutes=60,
            notes="First time customer",
            confirmation_sent=True
        )
        assert appointment.customer_email == "bob@example.com"
        assert appointment.service_type == "Consultation"
        assert appointment.appointment_datetime == future_time
        assert appointment.duration_minutes == 60
        assert appointment.notes == "First time customer"
        assert appointment.confirmation_sent is True
    
    def test_appointment_data_validation_empty_customer_name(self):
        """Test validation fails for empty customer_name."""
        appointment = AppointmentData(customer_name="", customer_phone="+1234567890")
        with pytest.raises(ValueError, match="customer_name cannot be empty"):
            appointment.validate()
    
    def test_appointment_data_validation_empty_customer_phone(self):
        """Test validation fails for empty customer_phone."""
        appointment = AppointmentData(customer_name="Bob Johnson", customer_phone="")
        with pytest.raises(ValueError, match="customer_phone cannot be empty"):
            appointment.validate()
    
    def test_appointment_data_validation_empty_service_type(self):
        """Test validation fails for empty service_type."""
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890",
            service_type=""
        )
        with pytest.raises(ValueError, match="service_type cannot be empty"):
            appointment.validate()
    
    def test_appointment_data_validation_negative_duration(self):
        """Test validation fails for negative duration_minutes."""
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890",
            service_type="Consultation",
            duration_minutes=-10
        )
        with pytest.raises(ValueError, match="duration_minutes must be positive"):
            appointment.validate()
    
    def test_appointment_data_validation_past_datetime(self):
        """Test validation fails for past appointment_datetime."""
        past_time = datetime.now(timezone.utc) - timedelta(days=1)
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890",
            service_type="Consultation",
            appointment_datetime=past_time
        )
        with pytest.raises(ValueError, match="appointment_datetime cannot be in the past"):
            appointment.validate()
    
    def test_appointment_data_validation_invalid_email(self):
        """Test validation fails for invalid customer_email."""
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890",
            service_type="Consultation",
            customer_email="invalid-email"
        )
        with pytest.raises(ValueError, match="customer_email must be a valid email address"):
            appointment.validate()
    
    def test_appointment_data_validation_valid(self):
        """Test validation passes for valid AppointmentData."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        appointment = AppointmentData(
            customer_name="Bob Johnson",
            customer_phone="+1234567890",
            service_type="Consultation",
            appointment_datetime=future_time,
            customer_email="bob@example.com"
        )
        appointment.validate()  # Should not raise
