"""Health and metadata routes for Vera Message Engine."""

import os
from datetime import datetime, timezone

from fastapi import APIRouter

from models.schemas import HealthResponse, MetadataResponse


router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status with current timestamp
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


@router.get("/metadata", response_model=MetadataResponse)
async def get_metadata():
    """Get bot metadata.
    
    Returns:
        Metadata including bot name, version, model, and capabilities
    """
    return MetadataResponse(
        bot_name=os.getenv("BOT_NAME", "Vera Message Engine"),
        version=os.getenv("BOT_VERSION", "1.0.0"),
        author=os.getenv("AUTHOR_NAME", "Rakesh Penugonda"),
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        provider=os.getenv("LLM_PROVIDER", "groq"),
        capabilities=["context", "tick", "reply"],
        supported_categories=["dentist", "salon", "restaurant", "gym", "pharmacy"]
    )