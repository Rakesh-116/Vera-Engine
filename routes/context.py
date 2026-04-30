"""Context storage routes for Vera Message Engine."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.schemas import ContextRequest, ContextResponse
from core.state_store import store


router = APIRouter()


@router.post("/context", response_model=ContextResponse)
async def store_context(request: ContextRequest):
    """Store merchant/customer/trigger context.
    
    This endpoint is idempotent - storing the same scope + context_id + version
    will return accepted:true with no actual storage change.
    
    Args:
        request: Context request with scope, context_id, version, payload
        
    Returns:
        Acknowledgment with ack_id and stored_at timestamp
    """
    # Validate scope - spec accepts all 4 scopes
    valid_scopes = ["category", "merchant", "customer", "trigger"]
    if request.scope not in valid_scopes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scope. Must be one of: {valid_scopes}"
        )
    
    # Store in state store
    stored = store.set(
        scope=request.scope,
        context_id=request.context_id,
        version=request.version,
        payload=request.payload,
        delivered_at=request.delivered_at
    )
    
    # Generate acknowledgment ID
    ack_id = f"ack_{uuid.uuid4().hex[:8]}"
    
    # Get stored timestamp
    entry = store.get(request.scope, request.context_id)
    stored_at = entry["stored_at"] if entry else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    return ContextResponse(
        accepted=True,  # Always accepted if valid request
        ack_id=ack_id,
        stored_at=stored_at
    )