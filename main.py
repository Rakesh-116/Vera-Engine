"""Vera Message Engine - FastAPI Application.

Main entry point for the Vera Message Engine service.
Routes all API endpoints under /v1 prefix.
"""

import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Import routes
from routes import health, context, tick, reply

# Create FastAPI app
app = FastAPI(
    title=os.getenv("BOT_NAME", "Vera Message Engine"),
    version=os.getenv("BOT_VERSION", "1.0.0"),
    description="AI assistant for merchant growth - magicpin AI Challenge"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/v1", tags=["Health"])
app.include_router(context.router, prefix="/v1", tags=["Context"])
app.include_router(tick.router, prefix="/v1", tags=["Tick"])
app.include_router(reply.router, prefix="/v1", tags=["Reply"])


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "Vera Message Engine API",
        "docs": "/docs",
        "health": "/v1/healthz",
        "metadata": "/v1/metadata"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )