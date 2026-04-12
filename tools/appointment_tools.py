"""Tool definitions for appointment management."""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Tool definition for OpenAI Realtime API."""
    type: str = "function"
    name: str
    description: str
    parameters: Dict[str, Any]


# RAG Tool (Knowledge Base Search)
from tools.rag_tool import SEARCH_KNOWLEDGE_BASE_TOOL

RAG_TOOLS = [SEARCH_KNOWLEDGE_BASE_TOOL]


# Appointment Management Tools
APPOINTMENT_TOOLS = [
    ToolDefinition(
        name="check_availability",
        description="Check if appointment slots are available for a given date and service type. Use this before booking to verify availability.",
        parameters={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g., 2026-04-15)"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service (e.g., haircut, coloring, consultation, massage, dental, repair)"
                }
            },
            "required": ["date"]
        }
    ),
    ToolDefinition(
        name="get_available_slots",
        description="Get a list of available time slots for a specific date. Returns up to 5 available times the customer can choose from.",
        parameters={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service (optional)"
                }
            },
            "required": ["date"]
        }
    ),
    ToolDefinition(
        name="book_appointment",
        description="Book an appointment for a customer. Only call this after confirming all details with the customer and verifying availability.",
        parameters={
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's full name"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer's phone number in E.164 format (e.g., +1234567890)"
                },
                "date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format"
                },
                "time": {
                    "type": "string",
                    "description": "Appointment time in HH:MM format (24-hour, e.g., 14:00 for 2 PM)"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service being booked"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duration in minutes (default: 30)"
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or special requests"
                }
            },
            "required": ["customer_name", "customer_phone", "date", "time", "service_type"]
        }
    )
]


# Lead Management Tools
LEAD_TOOLS = [
    ToolDefinition(
        name="create_lead",
        description="Create a sales lead when a customer expresses interest in services or products. Use this for sales inquiries, pricing questions, or when customer wants more information.",
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer's name"
                },
                "phone": {
                    "type": "string",
                    "description": "Customer's phone number"
                },
                "email": {
                    "type": "string",
                    "description": "Customer's email address (if provided)"
                },
                "inquiry_details": {
                    "type": "string",
                    "description": "Details about what the customer is interested in"
                },
                "budget": {
                    "type": "string",
                    "description": "Budget indication if mentioned (e.g., 'under $500', '$1000-2000')"
                },
                "timeline": {
                    "type": "string",
                    "description": "When customer wants to proceed (e.g., 'this week', 'next month', 'just browsing')"
                },
                "lead_score": {
                    "type": "integer",
                    "description": "Lead quality score from 1-10 based on urgency and budget (default: 5)"
                }
            },
            "required": ["name", "phone", "inquiry_details"]
        }
    )
]


# Customer Service Tools
CUSTOMER_TOOLS = [
    ToolDefinition(
        name="get_customer_history",
        description="Look up a customer's previous calls and appointments. Use this for returning customers to provide personalized service.",
        parameters={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Customer's phone number (optional if already in call context)"
                }
            },
            "required": []
        }
    ),
    ToolDefinition(
        name="send_sms",
        description="Send an SMS message to a customer. Use for sending information, confirmations, or follow-ups.",
        parameters={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Recipient's phone number"
                },
                "message": {
                    "type": "string",
                    "description": "Message text to send (keep under 160 characters for single SMS)"
                }
            },
            "required": ["phone", "message"]
        }
    )
]


# Combine all tools
ALL_TOOLS = RAG_TOOLS + APPOINTMENT_TOOLS + LEAD_TOOLS + CUSTOMER_TOOLS
