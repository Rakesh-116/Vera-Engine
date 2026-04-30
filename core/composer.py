"""The Brain - Message Composer for Vera Message Engine.

This is the core compose() function that decides what message Vera should send.
It combines merchant context, trigger data, and category-specific rules to 
generate the perfect next message for each merchant.
"""

import json
import os
from datetime import datetime
from typing import Any, Optional

from core.llm_client import llm_client
from core.prompts import build_system_prompt, build_user_prompt, build_reply_prompt, detect_reply_intent


# Supported categories
SUPPORTED_CATEGORIES = ["dentist", "salon", "restaurant", "gym", "pharmacy"]


async def compose(
    category: str,
    merchant: Optional[dict[str, Any]],
    trigger: Optional[dict[str, Any]],
    customer: Optional[dict[str, Any]],
    merchant_id: str = "unknown"
) -> dict[str, Any]:
    """Compose the best next message for a merchant.
    
    This is THE BRAIN of Vera Message Engine. It:
    1. Builds a category-specific system prompt
    2. Builds a user prompt with all available context
    3. Calls the LLM with structured JSON output
    4. Parses and returns the message object
    
    Args:
        category: Merchant category (dentist, salon, restaurant, gym, pharmacy)
        merchant: Full merchant context from state_store
        trigger: Trigger context if available
        customer: Customer context if available
        merchant_id: Merchant identifier for suppression key
        
    Returns:
        Dict with body, cta, send_as, suppression_key, rationale
    """
    # Default category if not supported
    if category.lower() not in SUPPORTED_CATEGORIES:
        category = "dentist"  # Default fallback
    
    # Build prompts
    system_prompt = build_system_prompt(category)
    user_prompt = build_user_prompt(merchant, trigger, customer)
    
    # Call LLM
    try:
        response_text = await llm_client.complete(
            system=system_prompt,
            user=user_prompt,
            json_mode=True
        )
        
        # Parse JSON response
        message = json.loads(response_text)
        
        # Validate and set defaults
        return _validate_message(message, merchant_id, category)
    
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return a fallback message
        return _fallback_message(merchant_id, category, "JSON parse error")
    except Exception as e:
        # Handle other errors gracefully
        return _fallback_message(merchant_id, category, str(e))


async def compose_reply(
    original_message: dict[str, Any],
    reply_text: str,
    reply_intent: Optional[str] = None,
    merchant_id: str = "unknown"
) -> dict[str, Any]:
    """Compose a reply to the merchant's response.
    
    Args:
        original_message: The message that was originally sent
        reply_text: The merchant's reply
        reply_intent: Optional intent hint
        merchant_id: Merchant identifier
        
    Returns:
        Dict with body, cta, send_as, suppression_key, rationale
    """
    # Detect intent if not provided
    if not reply_intent:
        reply_intent = detect_reply_intent(reply_text)
    
    # Build reply prompt
    system_prompt = """You are Vera, magicpin's AI assistant for merchant growth.
Your job: craft the perfect follow-up message based on the merchant's reply.

OUTPUT RULES:
- Return ONLY valid JSON, no markdown, no explanation
- Be concise and actionable
- Match the tone to the merchant's response

OUTPUT FORMAT:
{
  "body": "message text here",
  "cta": "CTA text here",
  "send_as": "Vera",
  "suppression_key": "unique:key:here",
  "rationale": "why this message now"
}"""
    
    user_prompt = build_reply_prompt(original_message, reply_text, reply_intent)
    
    try:
        response_text = await llm_client.complete(
            system=system_prompt,
            user=user_prompt,
            json_mode=True
        )
        
        message = json.loads(response_text)
        return _validate_message(message, merchant_id, "reply")
    
    except Exception as e:
        return _reply_fallback_message(merchant_id, reply_intent)


def _validate_message(
    message: dict[str, Any],
    merchant_id: str,
    category: str
) -> dict[str, Any]:
    """Validate and set defaults on message response.
    
    Args:
        message: Raw message from LLM
        merchant_id: Merchant identifier
        category: Merchant category
        
    Returns:
        Validated message dict
    """
    # Get current date for suppression key
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    return {
        "body": message.get("body", "Should I send you some updates?"),
        "cta": message.get("cta", "Yes"),
        "send_as": message.get("send_as", "Vera"),
        "suppression_key": message.get(
            "suppression_key", 
            f"{merchant_id}:{category}:{today}"
        ),
        "rationale": message.get(
            "rationale", 
            f"Category-specific message for {category}"
        )
    }


def _fallback_message(
    merchant_id: str,
    category: str,
    error: str
) -> dict[str, Any]:
    """Generate a fallback message when LLM fails.
    
    Args:
        merchant_id: Merchant identifier
        category: Merchant category
        error: Error description
        
    Returns:
        Fallback message dict
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    fallback_messages = {
        "dentist": "Your dental practice is ready for more patients. Want me to send a check-up offer to nearby customers?",
        "salon": "Your salon has availability this week. Should I notify nearby customers about your services?",
        "restaurant": "Your restaurant is ready for the lunch rush. Want me to send a special offer to nearby customers?",
        "gym": "More people in your area are looking for fitness options. Should I send them details about your gym?",
        "pharmacy": "Customers nearby might need your medicines. Want me to notify them about your pharmacy?"
    }
    
    return {
        "body": fallback_messages.get(category, "Ready to help you get more customers. Want me to send an offer?"),
        "cta": "Yes, send it",
        "send_as": "Vera",
        "suppression_key": f"{merchant_id}:fallback:{today}",
        "rationale": f"Fallback due to: {error}"
    }


def _reply_fallback_message(
    merchant_id: str,
    reply_intent: str
) -> dict[str, Any]:
    """Generate a fallback reply message.
    
    Args:
        merchant_id: Merchant identifier
        reply_intent: Detected reply intent
        
    Returns:
        Fallback reply message dict
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    intent_messages = {
        "approve": {
            "body": "Done! Your campaign is now live. You'll see results in your dashboard within 2 hours.",
            "cta": "View Campaign",
            "rationale": "Merchant approved - confirming action"
        },
        "decline": {
            "body": "No problem! Let me know when you're ready to try again.",
            "cta": "OK",
            "rationale": "Merchant declined - respecting their choice"
        },
        "question": {
            "body": "I'm happy to explain more. What would you like to know?",
            "cta": "Tell me more",
            "rationale": "Merchant has questions - offering clarification"
        },
        "modify": {
            "body": "I can modify that for you. What changes would you like?",
            "cta": "Edit message",
            "rationale": "Merchant wants to modify - inviting input"
        },
        "unknown": {
            "body": "Got it! Let me know if you'd like to make any changes.",
            "cta": "OK",
            "rationale": "Processing reply"
        }
    }
    
    message = intent_messages.get(reply_intent, intent_messages["unknown"])
    
    return {
        **message,
        "send_as": "Vera",
        "suppression_key": f"{merchant_id}:reply:{today}"
    }


def get_category_from_context(merchant: Optional[dict[str, Any]]) -> str:
    """Extract category from merchant context.
    
    Args:
        merchant: Merchant context dict
        
    Returns:
        Category string
    """
    if not merchant:
        return "dentist"  # Default
    
    # Try to get from identity
    if "identity" in merchant:
        category = merchant.get("identity", {}).get("category")
        if category:
            return category
    
    # Try direct category field
    if "category" in merchant:
        return merchant["category"]
    
    return "dentist"  # Default