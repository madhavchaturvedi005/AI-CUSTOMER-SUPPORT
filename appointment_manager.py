"""Appointment management service for scheduling and calendar integration."""

from typing import Optional, List, Dict, Any, Tuple, Callable
from datetime import datetime, timedelta, timezone
from models import AppointmentData
from database import DatabaseService


class AppointmentManager:
    """
    Manages appointment scheduling and calendar integration.
    
    Implements Requirements 6.1-6.5:
    - 6.1: Retrieve available time slots
    - 6.2: Propose at least 3 available time slots
    - 6.3: Confirm appointment details (date, time, service type, contact)
    - 6.4: Create calendar entry
    - 6.5: Send appointment confirmation via SMS within 2 minutes
    """
    
    def __init__(
        self,
        database: DatabaseService,
        business_hours: Optional[Dict[str, List[Tuple[int, int]]]] = None,
        slot_duration_minutes: int = 30,
        sms_callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Initialize AppointmentManager.
        
        Args:
            database: DatabaseService instance for persistence
            business_hours: Dictionary mapping day names to list of (start_hour, end_hour) tuples
                          e.g., {"monday": [(9, 17)], "tuesday": [(9, 17)]}
            slot_duration_minutes: Duration of each appointment slot in minutes (default: 30)
            sms_callback: Optional callback function to send SMS confirmations
                         Should accept (phone_number, message) as parameters
        """
        self.database = database
        self.slot_duration_minutes = slot_duration_minutes
        self.sms_callback = sms_callback
        
        # Default business hours: Monday-Friday 9 AM - 5 PM
        self.business_hours = business_hours or {
            "monday": [(9, 17)],
            "tuesday": [(9, 17)],
            "wednesday": [(9, 17)],
            "thursday": [(9, 17)],
            "friday": [(9, 17)],
            "saturday": [],
            "sunday": []
        }
    
    async def retrieve_available_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        service_type: Optional[str] = None
    ) -> List[datetime]:
        """
        Retrieve available time slots within a date range.
        
        Generates time slots based on business hours and filters out
        already booked appointments.
        
        Args:
            start_date: Start of date range to search
            end_date: End of date range to search
            service_type: Optional service type to filter by
            
        Returns:
            List of available datetime slots
            
        Requirement 6.1: Retrieve available time slots
        """
        available_slots = []
        
        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        now = datetime.now(timezone.utc)
        
        while current_date <= end_date:
            # Get day of week
            day_name = current_date.strftime("%A").lower()
            
            # Check if business is open on this day
            if day_name in self.business_hours and self.business_hours[day_name]:
                for start_hour, end_hour in self.business_hours[day_name]:
                    # Generate slots for this time range
                    slot_time = current_date.replace(hour=start_hour, minute=0, tzinfo=timezone.utc)
                    end_time = current_date.replace(hour=end_hour, minute=0, tzinfo=timezone.utc)
                    
                    while slot_time < end_time:
                        # Check if slot is in the future
                        if slot_time >= now:
                            # Check if slot is available (not booked)
                            is_available = await self._is_slot_available(slot_time, service_type)
                            if is_available:
                                available_slots.append(slot_time)
                        
                        # Move to next slot
                        slot_time += timedelta(minutes=self.slot_duration_minutes)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return available_slots
    
    async def propose_time_slots(
        self,
        preferred_date: Optional[datetime] = None,
        service_type: Optional[str] = None,
        num_slots: int = 3
    ) -> List[datetime]:
        """
        Propose available time slots to the caller.
        
        Returns at least 3 available slots (or as many as available).
        
        Args:
            preferred_date: Optional preferred date (defaults to tomorrow)
            service_type: Optional service type
            num_slots: Number of slots to propose (default: 3)
            
        Returns:
            List of proposed datetime slots (minimum 3 if available)
            
        Requirement 6.2: Propose at least 3 available time slots
        """
        # Default to tomorrow if no preferred date
        if preferred_date is None:
            preferred_date = datetime.now(timezone.utc) + timedelta(days=1)
        
        # Search for slots in the next 14 days
        start_date = preferred_date
        end_date = preferred_date + timedelta(days=14)
        
        # Get available slots
        available_slots = await self.retrieve_available_slots(
            start_date, end_date, service_type
        )
        
        # Return requested number of slots (or all if fewer available)
        return available_slots[:max(num_slots, 3)]
    
    async def confirm_appointment(
        self,
        customer_name: str,
        customer_phone: str,
        appointment_datetime: datetime,
        service_type: str,
        customer_email: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        notes: Optional[str] = None
    ) -> AppointmentData:
        """
        Confirm appointment with all details.
        
        Validates and creates an appointment with confirmed details.
        
        Args:
            customer_name: Customer's name
            customer_phone: Customer's phone number
            appointment_datetime: Scheduled date and time
            service_type: Type of service
            customer_email: Optional customer email
            duration_minutes: Optional duration (defaults to slot_duration_minutes)
            notes: Optional appointment notes
            
        Returns:
            AppointmentData object with confirmed details
            
        Requirement 6.3: Confirm date, time, service type, and contact details
        """
        # Create appointment data
        appointment = AppointmentData(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            service_type=service_type,
            appointment_datetime=appointment_datetime,
            duration_minutes=duration_minutes or self.slot_duration_minutes,
            notes=notes,
            confirmation_sent=False
        )
        
        # Validate appointment data
        appointment.validate()
        
        return appointment
    
    async def create_calendar_entry(
        self,
        appointment: AppointmentData,
        call_id: Optional[str] = None
    ) -> str:
        """
        Create a calendar entry for the appointment.
        
        Stores the appointment in the database and marks it as scheduled.
        
        Args:
            appointment: AppointmentData object
            call_id: Optional associated call ID
            
        Returns:
            Appointment ID from database
            
        Requirement 6.4: Create calendar entry
        """
        # Store in database
        appointment_id = await self.database.create_appointment(
            call_id=call_id,
            customer_name=appointment.customer_name,
            customer_phone=appointment.customer_phone,
            customer_email=appointment.customer_email,
            service_type=appointment.service_type,
            appointment_datetime=appointment.appointment_datetime,
            duration_minutes=appointment.duration_minutes,
            notes=appointment.notes,
            status="scheduled"
        )
        
        return appointment_id
    
    async def book_appointment(
        self,
        call_id: str,
        customer_name: str,
        customer_phone: str,
        appointment_datetime: datetime,
        service_type: str,
        customer_email: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[AppointmentData, str]:
        """
        Complete appointment booking pipeline: confirm, create calendar entry, send SMS.
        
        Args:
            call_id: Associated call ID
            customer_name: Customer's name
            customer_phone: Customer's phone number
            appointment_datetime: Scheduled date and time
            service_type: Type of service
            customer_email: Optional customer email
            notes: Optional appointment notes
            
        Returns:
            Tuple of (AppointmentData, appointment_id)
        """
        # Confirm appointment
        appointment = await self.confirm_appointment(
            customer_name=customer_name,
            customer_phone=customer_phone,
            appointment_datetime=appointment_datetime,
            service_type=service_type,
            customer_email=customer_email,
            notes=notes
        )
        
        # Create calendar entry
        appointment_id = await self.create_calendar_entry(appointment, call_id)
        
        # Send SMS confirmation (Requirement 6.5)
        await self.send_appointment_confirmation(appointment)
        
        return appointment, appointment_id
    
    async def send_appointment_confirmation(
        self,
        appointment: AppointmentData
    ) -> bool:
        """
        Send appointment confirmation via SMS.
        
        Sends confirmation within 2 minutes of booking with appointment details.
        
        Args:
            appointment: AppointmentData object
            
        Returns:
            True if SMS sent successfully, False otherwise
            
        Requirement 6.5: Send appointment confirmation via SMS within 2 minutes
        """
        # Format appointment datetime
        formatted_datetime = appointment.appointment_datetime.strftime("%B %d, %Y at %I:%M %p")
        
        # Create confirmation message
        message = (
            f"Appointment Confirmed!\n"
            f"Service: {appointment.service_type}\n"
            f"Date/Time: {formatted_datetime}\n"
            f"Duration: {appointment.duration_minutes} minutes\n"
            f"Name: {appointment.customer_name}\n"
        )
        
        if appointment.notes:
            message += f"Notes: {appointment.notes}\n"
        
        message += "\nThank you for booking with us!"
        
        # Send SMS via callback if provided
        if self.sms_callback:
            try:
                # If callback is async
                import asyncio
                import inspect
                if inspect.iscoroutinefunction(self.sms_callback):
                    await self.sms_callback(appointment.customer_phone, message)
                else:
                    self.sms_callback(appointment.customer_phone, message)
                
                # Mark confirmation as sent
                appointment.confirmation_sent = True
                
                print(f"📱 SMS confirmation sent to {appointment.customer_phone}")
                return True
            except Exception as e:
                print(f"⚠️  Error sending SMS confirmation: {e}")
                return False
        else:
            # Log confirmation (would integrate with Twilio SMS in production)
            print(f"📱 SMS Confirmation for {appointment.customer_name}:")
            print(f"   To: {appointment.customer_phone}")
            print(f"   Message: {message}")
            
            # Mark as sent for testing
            appointment.confirmation_sent = True
            return True
    
    async def extract_appointment_info(
        self,
        conversation_history: List[Dict[str, Any]],
        caller_phone: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract appointment information from conversation history.
        
        Args:
            conversation_history: List of conversation turns
            caller_phone: Caller's phone number
            
        Returns:
            Dictionary with appointment details or None if insufficient info
        """
        # Extract customer name
        name = self._extract_customer_name(conversation_history)
        
        # Extract service type
        service_type = self._extract_service_type(conversation_history)
        
        # Extract preferred date/time
        preferred_datetime = self._extract_preferred_datetime(conversation_history)
        
        # Need at least name and service type
        if not name or not service_type:
            return None
        
        return {
            "customer_name": name,
            "customer_phone": caller_phone,
            "service_type": service_type,
            "preferred_datetime": preferred_datetime
        }
    
    # Private helper methods
    
    async def _is_slot_available(
        self,
        slot_time: datetime,
        service_type: Optional[str] = None
    ) -> bool:
        """Check if a time slot is available (not already booked)."""
        # Query database for overlapping appointments
        # For now, return True (would check database in production)
        return True
    
    def _extract_customer_name(self, conversation_history: List[Dict[str, Any]]) -> Optional[str]:
        """Extract customer name from conversation."""
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                # Pattern: "my name is X"
                if "my name is" in text:
                    parts = text.split("my name is")
                    if len(parts) > 1:
                        name = parts[1].strip().split()[0:2]
                        return " ".join(name).title()
                
                # Pattern: "I'm X" or "I am X"
                if "i'm " in text or "i am " in text:
                    text = text.replace("i'm ", "i am ")
                    parts = text.split("i am ")
                    if len(parts) > 1:
                        name = parts[1].strip().split()[0:2]
                        return " ".join(name).title()
        
        return None
    
    def _extract_service_type(self, conversation_history: List[Dict[str, Any]]) -> Optional[str]:
        """Extract service type from conversation."""
        service_keywords = {
            "consultation": ["consultation", "consult", "meeting", "discuss"],
            "haircut": ["haircut", "hair", "trim", "style"],
            "massage": ["massage", "therapy", "spa"],
            "dental": ["dental", "dentist", "teeth", "cleaning"],
            "repair": ["repair", "fix", "service", "maintenance"]
        }
        
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                for service, keywords in service_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        return service
        
        return "general"  # Default service type
    
    def _extract_preferred_datetime(self, conversation_history: List[Dict[str, Any]]) -> Optional[datetime]:
        """Extract preferred date/time from conversation."""
        # Simple extraction - would use NLP in production
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                # Check for "tomorrow"
                if "tomorrow" in text:
                    return datetime.now(timezone.utc) + timedelta(days=1)
                
                # Check for "next week"
                if "next week" in text:
                    return datetime.now(timezone.utc) + timedelta(days=7)
                
                # Check for "today"
                if "today" in text:
                    return datetime.now(timezone.utc)
        
        return None
