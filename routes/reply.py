"""Reply routes for Vera Message Engine.

The /v1/reply endpoint handles merchant responses to Vera's messages.
Accepts spec-compliant payloads (message, from_role, turn_number) and custom fields.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from models.schemas import ReplyRequest, ReplyResponse, MessageContent
from core.composer import compose_reply


router = APIRouter()


# In-memory store for recent messages (for reply context)
_recent_messages: dict[str, dict] = {}


@router.post("/reply", response_model=ReplyResponse)
async def handle_reply(request: ReplyRequest):
    """Handle merchant's reply to Vera's message.
    
    Spec-compliant: accepts message, from_role, turn_number field names.
    Also supports custom field names (tick_id, merchant_id, reply_text).
    
    Args:
        request: Reply request (spec or custom fields)
        
    Returns:
        Reply response with next message and conversation state
    """
    # Get reply text from spec-compliant or custom fields
    reply_text = request.message or request.reply_text or ""
    
    # Get tick_id - use spec or custom field
    tick_id = request.tick_id or f"reply_{uuid.uuid4().hex[:8]}"
    
    # Get merchant_id
    merchant_id = request.merchant_id or "default"
    
    # Get reply intent from custom field or detect from message
    reply_intent = request.reply_intent
    
    # Look up the original message by tick_id
    original_message = _recent_messages.get(tick_id)
    
    if not original_message:
        # If no original message found, return a default response
        return ReplyResponse(
            tick_id=tick_id,
            next_message=MessageContent(
                body="Thanks for your message! How can I help you grow your business today?",
                cta="Tell me more",
                send_as="Vera",
                suppression_key=f"{merchant_id}:reply_fallback:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                rationale="No original message found - sending welcome"
            ),
            conversation_state="unknown",
            responded_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
    
    # Compose the reply
    try:
        next_message = await compose_reply(
            original_message=original_message,
            reply_text=reply_text,
            reply_intent=reply_intent,
            merchant_id=merchant_id
        )
        
        # Determine conversation state based on intent
        conversation_state = _determine_conversation_state(reply_text, next_message.get("rationale", ""))
        
        # Store this message for potential follow-up
        _recent_messages[tick_id] = next_message
        
        return ReplyResponse(
            tick_id=tick_id,
            next_message=MessageContent(**next_message),
            conversation_state=conversation_state,
            responded_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
    
    except Exception as e:
        # If reply composition fails, return error message
        return ReplyResponse(
            tick_id=tick_id,
            next_message=MessageContent(
                body="Thanks for your response! Let me know if you'd like help with anything else.",
                cta="OK",
                send_as="Vera",
                suppression_key=f"{merchant_id}:error:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                rationale=f"Error: {str(e)}"
            ),
            conversation_state="error",
            responded_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )


def _determine_conversation_state(reply_text: str, rationale: str) -> str:
    """Determine the conversation state based on reply.
    
    Args:
        reply_text: The merchant's reply text
        rationale: The rationale from message composition
        
    Returns:
        Conversation state string
    """
    if not reply_text:
        return "unknown"
    
    reply_lower = reply_text.lower()
    
    # Check for approval keywords
    approval_keywords = ["yes", "go ahead", "sure", "ok", "do it", "send", "activate", "run", "perfect", "good"]
    if any(kw in reply_lower for kw in approval_keywords):
        return "campaign_launched"
    
    # Check for decline keywords
    decline_keywords = ["no", "not now", "later", "skip", "don't", "stop", "cancel"]
    if any(kw in reply_lower for kw in decline_keywords):
        return "declined"
    
    # Check for questions
    if any(kw in reply_lower for kw in ["what", "how", "why", "explain", "tell me"]):
        return "question"
    
    # Check for modification requests
    if any(kw in reply_lower for kw in ["change", "modify", "edit", "different", "instead"]):
        return "modifying"
    
    return "ongoing"


def store_message_for_reply(tick_id: str, message: dict) -> None:
    """Store a message so it can be referenced in replies.
    
    Args:
        tick_id: The tick identifier
        message: The message dict to store
    """
    _recent_messages[tick_id] = message