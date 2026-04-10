"""Lead management service for capturing and qualifying leads."""

from typing import Optional, Dict, Any, Tuple, Callable
from datetime import datetime, timezone
from models import LeadData, Intent
from database import DatabaseService


class LeadManager:
    """
    Manages lead capture, qualification, and scoring.
    
    Implements Requirements 5.1-5.5:
    - 5.1: Collect caller name, contact number, and inquiry details
    - 5.2: Qualify leads based on budget, timeline, and decision authority
    - 5.3: Assign lead score from 1 to 10
    - 5.4: Store lead information in structured format
    - 5.5: Trigger notification for high-value leads (score >= 7)
    """
    
    def __init__(
        self,
        database: DatabaseService,
        notification_callback: Optional[Callable[[LeadData], None]] = None
    ):
        """
        Initialize LeadManager.
        
        Args:
            database: DatabaseService instance for persistence
            notification_callback: Optional callback function to trigger notifications
                                  for high-value leads. Should accept LeadData as parameter.
        """
        self.database = database
        self.notification_callback = notification_callback
    
    async def collect_lead_info(
        self,
        call_id: str,
        conversation_history: list[Dict[str, Any]],
        caller_phone: str
    ) -> Optional[LeadData]:
        """
        Collect lead information from conversation history.
        
        Extracts lead data from the conversation by analyzing the dialogue
        for name, contact information, and inquiry details.
        
        Args:
            call_id: Unique identifier for the call
            conversation_history: List of conversation turns
            caller_phone: Caller's phone number
            
        Returns:
            LeadData object if sufficient information collected, None otherwise
            
        Requirement 5.1: Collect caller name, contact number, and inquiry details
        """
        # Extract information from conversation
        name = self._extract_name(conversation_history)
        email = self._extract_email(conversation_history)
        inquiry_details = self._extract_inquiry_details(conversation_history)
        
        # Need at least name and inquiry to create a lead
        if not name or not inquiry_details:
            return None
        
        # Create lead data
        lead = LeadData(
            name=name,
            phone=caller_phone,
            email=email,
            inquiry_details=inquiry_details,
            source="voice_call"
        )
        
        return lead
    
    async def qualify_lead(
        self,
        lead: LeadData,
        conversation_history: list[Dict[str, Any]]
    ) -> LeadData:
        """
        Qualify lead based on budget, timeline, and decision authority.
        
        Analyzes conversation to determine:
        - Budget indication (low/medium/high)
        - Timeline (immediate/short-term/long-term)
        - Decision authority (can they make purchasing decisions)
        
        Args:
            lead: LeadData object to qualify
            conversation_history: List of conversation turns
            
        Returns:
            Updated LeadData with qualification information
            
        Requirement 5.2: Qualify leads based on budget, timeline, and decision authority
        """
        # Extract qualification criteria
        lead.budget_indication = self._extract_budget_indication(conversation_history)
        lead.timeline = self._extract_timeline(conversation_history)
        lead.decision_authority = self._extract_decision_authority(conversation_history)
        
        return lead
    
    async def score_lead(self, lead: LeadData) -> int:
        """
        Assign a lead score from 1 to 10 based on qualification criteria.
        
        Scoring algorithm:
        - Base score: 3
        - Budget indication: +3 (high), +2 (medium), +1 (low), 0 (none)
        - Timeline: +3 (immediate), +2 (short-term), +1 (long-term), 0 (none)
        - Decision authority: +2 (yes), 0 (no)
        - Email provided: +1
        
        Args:
            lead: LeadData object to score
            
        Returns:
            Lead score from 1 to 10
            
        Requirement 5.3: Assign lead score from 1 to 10
        """
        score = 3  # Base score
        
        # Budget indication scoring
        if lead.budget_indication:
            budget_lower = lead.budget_indication.lower()
            if "high" in budget_lower or "large" in budget_lower:
                score += 3
            elif "medium" in budget_lower or "moderate" in budget_lower:
                score += 2
            elif "low" in budget_lower or "small" in budget_lower:
                score += 1
        
        # Timeline scoring
        if lead.timeline:
            timeline_lower = lead.timeline.lower()
            if "immediate" in timeline_lower or "urgent" in timeline_lower or "asap" in timeline_lower:
                score += 3
            elif "short" in timeline_lower or "soon" in timeline_lower or "week" in timeline_lower:
                score += 2
            elif "long" in timeline_lower or "month" in timeline_lower or "quarter" in timeline_lower:
                score += 1
        
        # Decision authority scoring
        if lead.decision_authority:
            score += 2
        
        # Email provided scoring
        if lead.email:
            score += 1
        
        # Ensure score is within 1-10 range
        score = max(1, min(10, score))
        
        lead.lead_score = score
        return score
    
    async def save_lead(
        self,
        call_id: str,
        lead: LeadData
    ) -> str:
        """
        Store lead information in database.
        
        Args:
            call_id: Unique identifier for the call
            lead: LeadData object to store
            
        Returns:
            Lead ID from database
            
        Requirement 5.4: Store lead information in structured format
        """
        # Validate lead data
        lead.validate()
        
        # Store in database
        lead_id = await self.database.create_lead(
            call_id=call_id,
            name=lead.name,
            phone=lead.phone,
            email=lead.email,
            inquiry_details=lead.inquiry_details,
            budget_indication=lead.budget_indication,
            timeline=lead.timeline,
            decision_authority=lead.decision_authority,
            lead_score=lead.lead_score,
            source=lead.source
        )
        
        return lead_id
    
    def is_high_value_lead(self, lead: LeadData) -> bool:
        """
        Check if lead is high-value (score >= 7).
        
        Args:
            lead: LeadData object to check
            
        Returns:
            True if lead score >= 7, False otherwise
            
        Requirement 5.5: Identify high-value leads
        """
        return lead.lead_score >= 7
    
    async def process_lead(
        self,
        call_id: str,
        conversation_history: list[Dict[str, Any]],
        caller_phone: str
    ) -> Tuple[Optional[LeadData], bool]:
        """
        Complete lead processing pipeline: collect, qualify, score, and save.
        
        Also triggers notification for high-value leads (Requirement 5.5).
        
        Args:
            call_id: Unique identifier for the call
            conversation_history: List of conversation turns
            caller_phone: Caller's phone number
            
        Returns:
            Tuple of (LeadData, is_high_value) or (None, False) if no lead captured
        """
        # Collect lead information
        lead = await self.collect_lead_info(call_id, conversation_history, caller_phone)
        
        if not lead:
            return None, False
        
        # Qualify lead
        lead = await self.qualify_lead(lead, conversation_history)
        
        # Score lead
        await self.score_lead(lead)
        
        # Save lead
        await self.save_lead(call_id, lead)
        
        # Check if high-value
        is_high_value = self.is_high_value_lead(lead)
        
        # Trigger notification for high-value leads (Requirement 5.5)
        if is_high_value:
            await self.trigger_high_value_notification(lead)
        
        return lead, is_high_value
    
    async def trigger_high_value_notification(self, lead: LeadData) -> None:
        """
        Trigger immediate notification for high-value lead.
        
        Sends notification to sales team when a lead with score >= 7 is identified.
        
        Args:
            lead: High-value LeadData object
            
        Requirement 5.5: Send immediate notification to sales team for high-value leads
        """
        if not self.is_high_value_lead(lead):
            return
        
        # Call notification callback if provided
        if self.notification_callback:
            try:
                # If callback is async
                if hasattr(self.notification_callback, '__call__'):
                    import asyncio
                    import inspect
                    if inspect.iscoroutinefunction(self.notification_callback):
                        await self.notification_callback(lead)
                    else:
                        self.notification_callback(lead)
                
                print(f"🔔 High-value lead notification triggered for {lead.name} (score: {lead.lead_score})")
            except Exception as e:
                print(f"⚠️  Error triggering notification: {e}")
        else:
            # Log notification (would integrate with NotificationService in production)
            print(f"🔔 High-value lead detected: {lead.name} (score: {lead.lead_score})")
            print(f"   Phone: {lead.phone}")
            print(f"   Email: {lead.email}")
            print(f"   Inquiry: {lead.inquiry_details[:100]}...")
    
    # Private helper methods for information extraction
    
    def _extract_name(self, conversation_history: list[Dict[str, Any]]) -> Optional[str]:
        """Extract caller name from conversation."""
        # Look for patterns like "my name is X", "I'm X", "this is X"
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                # Pattern: "my name is X"
                if "my name is" in text:
                    parts = text.split("my name is")
                    if len(parts) > 1:
                        name = parts[1].strip().split()[0:2]  # Get first 2 words
                        return " ".join(name).title()
                
                # Pattern: "I'm X" or "I am X"
                if "i'm " in text or "i am " in text:
                    text = text.replace("i'm ", "i am ")
                    parts = text.split("i am ")
                    if len(parts) > 1:
                        name = parts[1].strip().split()[0:2]
                        return " ".join(name).title()
                
                # Pattern: "this is X"
                if "this is" in text:
                    parts = text.split("this is")
                    if len(parts) > 1:
                        name = parts[1].strip().split()[0:2]
                        return " ".join(name).title()
        
        return None
    
    def _extract_email(self, conversation_history: list[Dict[str, Any]]) -> Optional[str]:
        """Extract email address from conversation."""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "")
                matches = re.findall(email_pattern, text)
                if matches:
                    return matches[0]
        
        return None
    
    def _extract_inquiry_details(self, conversation_history: list[Dict[str, Any]]) -> str:
        """Extract inquiry details from conversation."""
        # Combine all caller messages to form inquiry details
        caller_messages = [
            turn.get("text", "")
            for turn in conversation_history
            if turn.get("speaker") == "caller"
        ]
        
        # Join and truncate to reasonable length
        inquiry = " ".join(caller_messages)
        return inquiry[:500] if inquiry else ""
    
    def _extract_budget_indication(self, conversation_history: list[Dict[str, Any]]) -> Optional[str]:
        """Extract budget indication from conversation."""
        budget_keywords = {
            "high": ["high budget", "large budget", "premium", "enterprise", "unlimited"],
            "medium": ["medium budget", "moderate budget", "standard", "typical"],
            "low": ["low budget", "small budget", "limited budget", "tight budget", "affordable"]
        }
        
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                for level, keywords in budget_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        return level
        
        return None
    
    def _extract_timeline(self, conversation_history: list[Dict[str, Any]]) -> Optional[str]:
        """Extract timeline from conversation."""
        timeline_keywords = {
            "immediate": ["immediate", "urgent", "asap", "right now", "today", "this week"],
            "short-term": ["soon", "next week", "next month", "short term", "quickly"],
            "long-term": ["long term", "next quarter", "next year", "eventually", "future"]
        }
        
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                for timeline, keywords in timeline_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        return timeline
        
        return None
    
    def _extract_decision_authority(self, conversation_history: list[Dict[str, Any]]) -> bool:
        """Extract decision authority from conversation."""
        authority_keywords = [
            "i can decide", "i make the decision", "i'm the owner", "i'm the manager",
            "i have authority", "i can approve", "it's my decision", "i'm the ceo",
            "i am the owner", "i am the manager", "i am the ceo", "i can make the decision"
        ]
        
        for turn in conversation_history:
            if turn.get("speaker") == "caller":
                text = turn.get("text", "").lower()
                
                if any(keyword in text for keyword in authority_keywords):
                    return True
        
        return False
