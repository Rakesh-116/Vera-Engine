"""Tick routes for Vera Message Engine.

The /v1/tick endpoint is the main message composition engine.
Accepts spec-compliant payloads with optional fields.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from models.schemas import TickRequest, TickResponse, MessageContent
from core.state_store import store
from core.composer import compose, get_category_from_context
from routes import reply


router = APIRouter()


@router.post("/tick", response_model=TickResponse)
async def tick(request: TickRequest):
    """Decide what message Vera should send next.
    
    Spec-compliant: accepts payloads without merchant_id, tick_id, timestamp.
    All fields are optional - works with empty {} payload.
    
    Args:
        request: Tick request (all fields optional)
        
    Returns:
        Tick response with composed message or should_send=false
    """
    # Generate tick_id if not provided
    tick_id = request.tick_id or f"tick_{uuid.uuid4().hex[:8]}"
    
    # Load contexts from state store
    merchant_context = None
    trigger_context = None
    customer_context = None
    
    # Get merchant context (use merchant_id if provided)
    if request.merchant_id:
        merchant_entry = store.get("merchant", request.merchant_id)
        if merchant_entry:
            merchant_context = merchant_entry["payload"]
    
    # Get trigger context (use trigger_id if provided)
    if request.trigger_id:
        trigger_entry = store.get("trigger", request.trigger_id)
        if trigger_entry:
            trigger_context = trigger_entry["payload"]
    
    # Get customer context
    if request.customer_id:
        customer_entry = store.get("customer", request.customer_id)
        if customer_entry:
            customer_context = customer_entry["payload"]
    
    # If no merchant context, try to get from category scope
    if not merchant_context:
        category_entry = store.get("category", "default")
        if category_entry:
            merchant_context = category_entry["payload"]
    
    # If still no context, return a default message
    if not merchant_context:
        return TickResponse(
            tick_id=tick_id,
            should_send=True,
            message=MessageContent(
                body="Hi! I'm Vera, your AI assistant for merchant growth. Would you like help with your business?",
                cta="Yes",
                send_as="Vera",
                suppression_key=f"default_welcome:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                rationale="No context available - sending welcome message"
            ),
            composed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
    
    # Get category from merchant context
    category = get_category_from_context(merchant_context)
    
    # Compose the message
    try:
        message = await compose(
            category=category,
            merchant=merchant_context,
            trigger=trigger_context,
            customer=customer_context,
            merchant_id=request.merchant_id or "default"
        )
        
        # Store message for reply context
        reply.store_message_for_reply(tick_id, message)
        
        return TickResponse(
            tick_id=tick_id,
            should_send=True,
            message=MessageContent(**message),
            composed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
    
    except Exception as e:
        # If composition fails, return a fallback message
        return TickResponse(
            tick_id=tick_id,
            should_send=True,
            message=MessageContent(
                body="I'd like to help you grow your business. Would you like to set up a campaign?",
                cta="Yes",
                send_as="Vera",
                suppression_key=f"fallback:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                rationale=f"Error occurred: {str(e)}"
            ),
            composed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )