"""System prompts for Vera Message Engine.

Contains category-specific prompts and user prompt builders.
"""

from typing import Any, Optional


# Category-specific tone and style rules
CATEGORY_RULES = {
    "dentist": """
You write for a dental clinic. Tone: clinical, professional, trust-building.
- Lead with patient volume data, health outcomes, search trends
- Never use pushy sales language
- Strong openers: patient counts, health awareness, local demand
- Avoid: "discount", "cheap", "hurry"
- Good CTA: "Should I send this to nearby patients?" / "Want me to activate this?"
""",
    "salon": """
You write for a beauty salon. Tone: aspirational, trend-aware, friendly.
- Use seasonal hooks (festival season, wedding season, summer looks)
- Visual language, specific service names
- Good CTA: "Should I book these slots?" / "Want to run this today?"
""",
    "restaurant": """
You write for a restaurant. Tone: hunger-driven, time-sensitive, local.
- Use meal times (lunch rush, dinner window), crowd data, dish names
- Urgency language works here
- Good CTA: "Should I send this now?" / "Activate lunch offer?"
""",
    "gym": """
You write for a fitness center. Tone: motivational, goal-oriented, metric-driven.
- Use attendance data, member counts, challenge language
- Good CTA: "Should I send this to nearby fitness seekers?"
""",
    "pharmacy": """
You write for a pharmacy. Tone: utility-first, informational, health-aware.
- Use seasonal demand (monsoon, cold season), medicine awareness
- Never make health claims or diagnoses
- Good CTA: "Should I notify nearby customers?" / "Want to run this health reminder?"
"""
}


def build_system_prompt(category: str) -> str:
    """Build the system prompt based on category.
    
    Args:
        category: The merchant category (dentist, salon, restaurant, gym, pharmacy)
        
    Returns:
        Complete system prompt string
    """
    category_rules = CATEGORY_RULES.get(
        category.lower(), 
        "Use professional, friendly tone."
    )
    
    return f"""You are Vera, magicpin's AI assistant for merchant growth.
Your job: craft ONE perfect message + CTA that a merchant will want to act on immediately.

CATEGORY RULES:
{category_rules}

OUTPUT RULES:
- Return ONLY valid JSON, no markdown, no explanation
- Use REAL numbers, offer prices, dates from the context given
- One message body (1-2 sentences max)
- One CTA (yes/no action, under 6 words)
- Never hallucinate facts not in the context
- suppression_key format: merchant_id:topic:date

OUTPUT FORMAT:
{{
  "body": "message text here",
  "cta": "CTA text here",
  "send_as": "Vera",
  "suppression_key": "unique:key:here",
  "rationale": "why this message now"
}}"""


def build_user_prompt(
    merchant: Optional[dict[str, Any]], 
    trigger: Optional[dict[str, Any]], 
    customer: Optional[dict[str, Any]]
) -> str:
    """Build the user prompt with all available context.
    
    Args:
        merchant: Merchant context dict
        trigger: Trigger context dict
        customer: Customer context dict
        
    Returns:
        Complete user prompt string
    """
    parts = []
    
    # Always include merchant context if available
    if merchant:
        parts.append("=== MERCHANT CONTEXT ===")
        parts.append(_format_merchant_context(merchant))
    else:
        parts.append("=== MERCHANT CONTEXT ===")
        parts.append("No merchant context available")
    
    # Add trigger context if available
    if trigger:
        parts.append("=== TRIGGER ===")
        parts.append(_format_trigger_context(trigger))
    
    # Add customer context if available
    if customer:
        parts.append("=== CUSTOMER CONTEXT ===")
        parts.append(str(customer))
    
    parts.append("=== TASK ===\nCompose the best next message for this merchant right now.")
    
    return "\n".join(parts)


def _format_merchant_context(merchant: dict[str, Any]) -> str:
    """Format merchant context for the prompt.
    
    Args:
        merchant: Raw merchant context
        
    Returns:
        Formatted string representation
    """
    lines = []
    
    # Handle different merchant context structures
    if "identity" in merchant:
        identity = merchant.get("identity", {})
        lines.append(f"Name: {identity.get('name', 'Unknown')}")
        lines.append(f"Category: {identity.get('category', 'Unknown')}")
        lines.append(f"Locality: {identity.get('locality', 'Unknown')}")
    
    if "performance" in merchant:
        perf = merchant.get("performance", {})
        lines.append(f"Rating: {perf.get('rating', 'N/A')}")
        lines.append(f"Reviews: {perf.get('reviews', 'N/A')}")
        lines.append(f"Monthly Visits: {perf.get('monthly_visits', 'N/A')}")
        lines.append(f"Visit Trend: {perf.get('visit_trend', 'N/A')}")
    
    if "offers" in merchant:
        offers = merchant.get("offers", [])
        if offers:
            lines.append("Active Offers:")
            for offer in offers:
                if isinstance(offer, dict):
                    lines.append(
                        f"  - {offer.get('name', 'Unknown')}: "
                        f"₹{offer.get('price', 'N/A')} (was ₹{offer.get('original', 'N/A')})"
                    )
    
    # Fallback: if merchant is a simple dict
    if not lines:
        lines.append(str(merchant))
    
    return "\n".join(lines)


def _format_trigger_context(trigger: dict[str, Any]) -> str:
    """Format trigger context for the prompt.
    
    Args:
        trigger: Raw trigger context
        
    Returns:
        Formatted string representation
    """
    lines = []
    
    if "type" in trigger:
        lines.append(f"Type: {trigger.get('type')}")
    if "signal" in trigger:
        lines.append(f"Signal: {trigger.get('signal')}")
    if "urgency" in trigger:
        lines.append(f"Urgency: {trigger.get('urgency')}")
    if "timestamp" in trigger:
        lines.append(f"Timestamp: {trigger.get('timestamp')}")
    
    # Fallback
    if not lines:
        lines.append(str(trigger))
    
    return "\n".join(lines)


def build_reply_prompt(
    original_message: dict[str, Any],
    reply_text: str,
    reply_intent: Optional[str] = None
) -> str:
    """Build prompt for reply handling.
    
    Args:
        original_message: The original message that was sent
        reply_text: The merchant's reply
        reply_intent: Optional intent hint
        
    Returns:
        User prompt for reply composition
    """
    parts = [
        "=== ORIGINAL MESSAGE ===",
        f"Body: {original_message.get('body', '')}",
        f"CTA: {original_message.get('cta', '')}",
        "",
        "=== MERCHANT REPLY ===",
        reply_text,
    ]
    
    if reply_intent:
        parts.extend([
            "",
            f"Detected Intent: {reply_intent}"
        ])
    
    parts.extend([
        "",
        "=== TASK ===",
        "Compose the appropriate next message based on the merchant's reply."
    ])
    
    return "\n".join(parts)


# Reply intent patterns for simple classification
REPLY_INTENT_PATTERNS = {
    "approve": ["yes", "go ahead", "sure", "ok", "do it", "send", "activate", "run"],
    "decline": ["no", "not now", "later", "skip", "don't", "stop"],
    "question": ["what", "how", "explain", "tell me more", "details"],
    "modify": ["change", "modify", "edit", "different", "instead"],
}


def detect_reply_intent(reply_text: str) -> str:
    """Simple keyword-based intent detection.
    
    Args:
        reply_text: The merchant's reply text
        
    Returns:
        Detected intent category
    """
    reply_lower = reply_text.lower()
    
    for intent, keywords in REPLY_INTENT_PATTERNS.items():
        for keyword in keywords:
            if keyword in reply_lower:
                return intent
    
    return "unknown"