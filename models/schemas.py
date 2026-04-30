"""Pydantic models for Vera Message Engine API."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ==================== Health & Metadata ====================


class HealthResponse(BaseModel):
    """Response model for /v1/healthz endpoint."""
    status: str = Field(default="ok", description="Health status")
    timestamp: str = Field(description="ISO timestamp of health check")


class MetadataResponse(BaseModel):
    """Response model for /v1/metadata endpoint."""
    bot_name: str = Field(default="Vera Message Engine")
    version: str = Field(default="1.0.0")
    author: str = Field(default="Rakesh Penugonda")
    model: str = Field(default="llama-3.3-70b-versatile")
    provider: str = Field(default="groq")
    capabilities: list[str] = Field(default_factory=lambda: ["context", "tick", "reply"])
    supported_categories: list[str] = Field(
        default_factory=lambda: ["dentist", "salon", "restaurant", "gym", "pharmacy"]
    )


# ==================== Context ====================


class ContextRequest(BaseModel):
    """Request model for POST /v1/context endpoint.
    
    Spec: Four scopes - category, merchant, customer, trigger - all should be accepted.
    """
    scope: str = Field(description="Context scope: category, merchant, customer, or trigger")
    context_id: str = Field(description="Unique identifier for the context")
    version: int = Field(description="Version number for idempotency")
    payload: dict[str, Any] = Field(description="Arbitrary JSON payload")
    delivered_at: str = Field(description="ISO timestamp when context was delivered")


class ContextResponse(BaseModel):
    """Response model for POST /v1/context endpoint."""
    accepted: bool = Field(description="Whether context was accepted")
    ack_id: str = Field(description="Acknowledgment ID")
    stored_at: str = Field(description="ISO timestamp when stored")


# ==================== Tick ====================


class TickRequest(BaseModel):
    """Request model for POST /v1/tick endpoint.
    
    Spec: Should NOT require merchant_id, tick_id, timestamp fields.
    All fields are optional to accept spec-compliant payloads.
    """
    merchant_id: Optional[str] = Field(default=None, description="Optional merchant identifier")
    trigger_id: Optional[str] = Field(default=None, description="Optional trigger identifier")
    customer_id: Optional[str] = Field(default=None, description="Optional customer identifier")
    tick_id: Optional[str] = Field(default=None, description="Optional tick identifier")
    timestamp: Optional[str] = Field(default=None, description="Optional timestamp")


class MessageContent(BaseModel):
    """Message content structure."""
    body: str = Field(description="The message text")
    cta: str = Field(description="Call to action text")
    send_as: str = Field(default="Vera", description="Sender name")
    suppression_key: str = Field(description="Unique key to prevent duplicate sends")
    rationale: str = Field(description="Why this message was chosen")


class TickResponse(BaseModel):
    """Response model for POST /v1/tick endpoint."""
    tick_id: str = Field(description="The tick identifier")
    should_send: bool = Field(description="Whether a message should be sent")
    message: Optional[MessageContent] = Field(default=None, description="The composed message")
    composed_at: str = Field(description="ISO timestamp when composed")


# ==================== Reply ====================


class ReplyRequest(BaseModel):
    """Request model for POST /v1/reply endpoint.
    
    Spec: Should accept message, from_role, turn_number field names.
    Also supports custom field names for backward compatibility.
    """
    # Spec-compliant fields
    message: Optional[str] = Field(default=None, description="The reply message text")
    from_role: Optional[str] = Field(default=None, description="Role sending the reply")
    turn_number: Optional[int] = Field(default=None, description="Turn number in conversation")
    
    # Custom fields (for backward compatibility)
    tick_id: Optional[str] = Field(default=None, description="Optional tick identifier")
    merchant_id: Optional[str] = Field(default=None, description="Optional merchant identifier")
    reply_text: Optional[str] = Field(default=None, description="Optional reply text")
    reply_intent: Optional[str] = Field(default=None, description="Optional intent hint")
    timestamp: Optional[str] = Field(default=None, description="Optional timestamp")


class ReplyResponse(BaseModel):
    """Response model for POST /v1/reply endpoint."""
    tick_id: str = Field(description="The tick identifier")
    next_message: MessageContent = Field(description="The next message in the conversation")
    conversation_state: str = Field(description="Current conversation state")
    responded_at: str = Field(description="ISO timestamp when responded")


# ==================== Internal Models ====================


class MerchantIdentity(BaseModel):
    """Merchant identity information."""
    name: str
    category: str
    locality: str


class MerchantPerformance(BaseModel):
    """Merchant performance metrics."""
    rating: float
    reviews: int
    monthly_visits: int
    visit_trend: str


class Offer(BaseModel):
    """Merchant offer details."""
    id: str
    name: str
    price: int
    original: int
    active: bool


class MerchantContext(BaseModel):
    """Full merchant context structure."""
    identity: MerchantIdentity
    performance: MerchantPerformance
    offers: list[Offer]


class TriggerContext(BaseModel):
    """Trigger context structure."""
    type: str
    signal: str
    urgency: str
    timestamp: str


class CustomerContext(BaseModel):
    """Customer context structure."""
    # Flexible structure based on customer data
    pass