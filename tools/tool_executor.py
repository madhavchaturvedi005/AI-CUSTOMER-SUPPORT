"""Tool executor for handling AI agent function calls."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import json


class ToolExecutor:
    """Executes tools called by the AI agent."""
    
    def __init__(
        self,
        appointment_manager=None,
        database=None,
        lead_manager=None,
        vector_service=None
    ):
        """
        Initialize ToolExecutor with service dependencies.
        
        Args:
            appointment_manager: AppointmentManager instance
            database: DatabaseService instance
            lead_manager: LeadManager instance
            vector_service: VectorService instance for RAG
        """
        self.appointment_manager = appointment_manager
        self.database = database
        self.lead_manager = lead_manager
        self.vector_service = vector_service
        
        # Map tool names to execution functions
        self.tools = {
            "search_knowledge_base": self.search_knowledge_base,
            "check_availability": self.check_availability,
            "get_available_slots": self.get_available_slots,
            "book_appointment": self.book_appointment,
            "get_customer_history": self.get_customer_history,
            "send_sms": self.send_sms,
            "create_lead": self.create_lead
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        call_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from AI
            call_context: Optional call context for personalization
            
        Returns:
            Tool execution result with success status
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            print(f"🔧 Executing tool: {tool_name}")
            print(f"   Arguments: {json.dumps(arguments, indent=2)}")
            
            result = await self.tools[tool_name](arguments, call_context)
            
            print(f"✅ Tool result: {json.dumps(result, indent=2)}")
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            print(f"❌ Tool execution error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    async def search_knowledge_base(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search knowledge base using RAG."""
        if not self.vector_service:
            return {"error": "Vector service not available"}
        
        from tools.rag_tool import execute_search_knowledge_base
        return await execute_search_knowledge_base(args, self.vector_service)
    
    async def check_availability(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Check if appointment slot is available."""
        if not self.appointment_manager:
            return {"error": "Appointment manager not available"}
        
        date_str = args.get("date")
        service_type = args.get("service_type", "general")
        
        try:
            # Parse date
            appointment_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            
            # Check availability
            slots = await self.appointment_manager.retrieve_available_slots(
                start_date=appointment_date,
                end_date=appointment_date + timedelta(days=1),
                service_type=service_type
            )
            
            return {
                "available": len(slots) > 0,
                "slot_count": len(slots),
                "date": date_str,
                "service_type": service_type,
                "message": f"{'Yes' if len(slots) > 0 else 'No'}, we have {len(slots)} available slots for {service_type} on {date_str}"
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    async def get_available_slots(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get list of available time slots."""
        if not self.appointment_manager:
            return {"error": "Appointment manager not available"}
        
        date_str = args.get("date")
        service_type = args.get("service_type")
        
        try:
            appointment_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            
            slots = await self.appointment_manager.propose_time_slots(
                preferred_date=appointment_date,
                service_type=service_type,
                num_slots=5
            )
            
            # Format slots for AI
            formatted_slots = [
                slot.strftime("%I:%M %p") for slot in slots
            ]
            
            return {
                "date": date_str,
                "available_slots": formatted_slots,
                "count": len(formatted_slots),
                "message": f"Available times on {date_str}: {', '.join(formatted_slots)}" if formatted_slots else f"No available slots on {date_str}"
            }
        except Exception as e:
            return {
                "available_slots": [],
                "error": str(e)
            }
    
    async def book_appointment(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Book an appointment."""
        if not self.appointment_manager:
            return {"error": "Appointment manager not available"}
        
        try:
            # Parse datetime
            date_str = args.get("date")
            time_str = args.get("time")
            datetime_str = f"{date_str}T{time_str}:00Z"
            appointment_datetime = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            
            # Get call context
            call_id = context.get("call_id") if context else None
            
            # Book appointment
            appointment, appointment_id = await self.appointment_manager.book_appointment(
                call_id=call_id,
                customer_name=args.get("customer_name"),
                customer_phone=args.get("customer_phone"),
                appointment_datetime=appointment_datetime,
                service_type=args.get("service_type"),
                notes=args.get("notes", "")
            )
            
            formatted_date = appointment.appointment_datetime.strftime("%B %d, %Y")
            formatted_time = appointment.appointment_datetime.strftime("%I:%M %p")
            
            result = {
                "appointment_id": appointment_id,
                "customer_name": appointment.customer_name,
                "date": formatted_date,
                "time": formatted_time,
                "service": appointment.service_type,
                "confirmation_sent": appointment.confirmation_sent,
                "message": f"Appointment booked for {appointment.customer_name} on {formatted_date} at {formatted_time} for {appointment.service_type}. SMS confirmation {'sent' if appointment.confirmation_sent else 'pending'}."
            }
            
            # Broadcast appointment_booked event
            try:
                from event_broadcaster import broadcaster
                import asyncio
                asyncio.create_task(broadcaster.publish("appointment_booked", {
                    "call_sid": context.get("call_sid") if context else "",
                    "appointment_id": appointment_id,
                    "customer_name": appointment.customer_name,
                    "customer_phone": appointment.customer_phone,
                    "date": formatted_date,
                    "time": formatted_time,
                    "service": appointment.service_type,
                    "confirmation_sent": appointment.confirmation_sent
                }))
            except Exception as e:
                print(f"⚠️  Error broadcasting appointment event: {e}")
            
            return result
        except Exception as e:
            return {
                "booked": False,
                "error": str(e)
            }
    
    async def get_customer_history(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get customer's call and appointment history."""
        if not self.database:
            return {"error": "Database not available"}
        
        phone = args.get("phone") or (context.get("caller_phone") if context else None)
        
        if not phone:
            return {"error": "Phone number required"}
        
        try:
            # Get call history
            calls = await self.database.get_caller_history(phone, limit=5)
            
            # Get appointments (if method exists)
            appointments = []
            try:
                if hasattr(self.database, 'get_customer_appointments'):
                    appointments = await self.database.get_customer_appointments(phone, limit=5)
            except:
                pass
            
            # Format response
            last_call = None
            if calls and len(calls) > 0:
                last_call_data = calls[0]
                if 'started_at' in last_call_data:
                    last_call = last_call_data['started_at'].strftime("%B %d, %Y") if hasattr(last_call_data['started_at'], 'strftime') else str(last_call_data['started_at'])
            
            upcoming = [
                {
                    "date": appt.get("appointment_datetime").strftime("%B %d, %Y at %I:%M %p") if hasattr(appt.get("appointment_datetime"), 'strftime') else str(appt.get("appointment_datetime")),
                    "service": appt.get("service_type")
                }
                for appt in appointments
                if appt.get("status") == "scheduled"
            ]
            
            return {
                "phone": phone,
                "is_returning_customer": len(calls) > 0,
                "total_calls": len(calls),
                "total_appointments": len(appointments),
                "last_call_date": last_call,
                "upcoming_appointments": upcoming,
                "message": f"{'Returning' if len(calls) > 0 else 'New'} customer. {len(calls)} previous calls, {len(appointments)} appointments, {len(upcoming)} upcoming."
            }
        except Exception as e:
            return {
                "is_returning_customer": False,
                "error": str(e)
            }
    
    async def create_lead(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a sales lead."""
        if not self.lead_manager:
            return {"error": "Lead manager not available"}
        
        try:
            lead_id = await self.lead_manager.capture_lead(
                call_id=context.get("call_id") if context else None,
                name=args.get("name"),
                phone=args.get("phone"),
                email=args.get("email"),
                inquiry_details=args.get("inquiry_details", ""),
                budget_indication=args.get("budget"),
                timeline=args.get("timeline"),
                decision_authority=False,
                lead_score=args.get("lead_score", 5)
            )
            
            result = {
                "lead_id": lead_id,
                "name": args.get("name"),
                "score": args.get("lead_score", 5),
                "message": f"Lead created for {args.get('name')} with score {args.get('lead_score', 5)}/10"
            }
            
            # Broadcast lead_created event
            try:
                from event_broadcaster import broadcaster
                import asyncio
                asyncio.create_task(broadcaster.publish("lead_created", {
                    "call_sid": context.get("call_sid") if context else "",
                    "lead_id": lead_id,
                    "name": args.get("name"),
                    "phone": args.get("phone"),
                    "email": args.get("email"),
                    "score": args.get("lead_score", 5),
                    "inquiry_details": args.get("inquiry_details", "")
                }))
            except Exception as e:
                print(f"⚠️  Error broadcasting lead event: {e}")
            
            return result
        except Exception as e:
            return {
                "created": False,
                "error": str(e)
            }
    
    async def send_sms(
        self,
        args: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS message."""
        phone = args.get("phone")
        message = args.get("message")
        
        # TODO: Integrate with Twilio SMS API
        # For now, just log it
        print(f"📱 SMS to {phone}: {message}")
        
        return {
            "sent": True,
            "phone": phone,
            "message_length": len(message),
            "message": f"SMS queued for {phone}"
        }
