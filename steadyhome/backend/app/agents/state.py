"""
Conversation State and Session Models for SteadyHome Voice Helpline.
Tracks all 10 mandatory conversation variables from Section 7:
1. borrower_id
2. verified
3. payment_mode
4. intent_tag
5. now_override
6. days_overdue
7. transfer_reason
8. loan_status
9. verification_attempts
10. clarification_attempts
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.config import settings

class ChatMessage(BaseModel):
    role: str  # 'system' | 'agent' | 'customer' | 'tool'
    content: str
    spoken_text: Optional[str] = None
    agent_name: str = "Root Agent"
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class ToolExecutionEvent(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    agent_name: str
    timestamp: str

class ConversationState(BaseModel):
    session_id: str
    # 10 Mandatory Conversation Variables
    borrower_id: Optional[str] = None
    verified: bool = False
    payment_mode: Optional[str] = None
    intent_tag: Optional[str] = None
    now_override: str = Field(default_factory=lambda: settings.CURRENT_SIMULATED_NOW)
    days_overdue: int = 0
    transfer_reason: Optional[str] = None
    loan_status: Optional[str] = None
    verification_attempts: int = 0
    clarification_attempts: int = 0

    # Additional runtime state
    active_agent: str = "Root Agent"  # "Root Agent" or "EMI Service Sub-Agent"
    borrower_name: Optional[str] = None
    loan_id: Optional[str] = None
    loan_last_four: Optional[str] = None
    dob: Optional[str] = None
    emi_amount: Optional[float] = None
    due_date: Optional[str] = None
    late_fee: float = 0.0
    is_escalated: bool = False
    escalation_id: Optional[str] = None
    awaiting_confirmation: bool = False
    disclaimer_played: bool = False
    call_active: bool = True
    messages: List[ChatMessage] = Field(default_factory=list)
    tool_logs: List[ToolExecutionEvent] = Field(default_factory=list)

