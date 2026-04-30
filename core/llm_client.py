"""LLM Client for Vera Message Engine.

Supports multiple LLM providers (Groq, OpenAI) with easy switching.
Uses Groq as primary with OpenAI as fallback.
"""

import os
import json
from typing import Optional

import groq
from openai import AsyncOpenAI


class LLMClient:
    """Unified LLM client with provider abstraction.
    
    Supports Groq (primary) and OpenAI (fallback) providers.
    Easy to extend for additional providers.
    """
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "groq")
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self._groq_client = None
        self._openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Initialize provider clients based on configuration."""
        # Initialize Groq client
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            self._groq_client = groq.AsyncGroq(api_key=groq_api_key)
        
        # Initialize OpenAI client (for fallback)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self._openai_client = AsyncOpenAI(api_key=openai_api_key)
    
    async def complete(
        self, 
        system: str, 
        user: str, 
        json_mode: bool = True
    ) -> str:
        """Generate completion from LLM.
        
        Args:
            system: System prompt
            user: User prompt
            json_mode: Whether to request JSON output
            
        Returns:
            LLM response text
        """
        if self.provider == "groq":
            return await self._groq_complete(system, user, json_mode)
        elif self.provider == "openai":
            return await self._openai_complete(system, user, json_mode)
        else:
            # Default to Groq
            return await self._groq_complete(system, user, json_mode)
    
    async def _groq_complete(
        self, 
        system: str, 
        user: str, 
        json_mode: bool
    ) -> str:
        """Generate completion using Groq.
        
        Args:
            system: System prompt
            user: User prompt
            json_mode: Whether to request JSON output
            
        Returns:
            Groq response text
        """
        if not self._groq_client:
            raise RuntimeError("Groq client not initialized. Set GROQ_API_KEY.")
        
        # Build messages
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
        
        # Build kwargs
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for determinism
            "max_tokens": 1024,
        }
        
        # Add JSON mode if requested
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        # Make the request
        response = await self._groq_client.chat.completions.create(**kwargs)
        
        return response.choices[0].message.content
    
    async def _openai_complete(
        self, 
        system: str, 
        user: str, 
        json_mode: bool
    ) -> str:
        """Generate completion using OpenAI.
        
        Args:
            system: System prompt
            user: User prompt
            json_mode: Whether to request JSON output
            
        Returns:
            OpenAI response text
        """
        if not self._openai_client:
            raise RuntimeError("OpenAI client not initialized. Set OPENAI_API_KEY.")
        
        # Map Groq model to OpenAI model
        model_map = {
            "llama-3.3-70b-versatile": "gpt-4o-mini",
            "llama-3.1-70b-versatile": "gpt-4o-mini",
            "llama-3-70b-versatile": "gpt-4o-mini",
        }
        openai_model = model_map.get(self.model, "gpt-4o-mini")
        
        # Build messages
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
        
        # Build kwargs
        kwargs = {
            "model": openai_model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        
        # Add JSON mode if requested
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        # Make the request
        response = await self._openai_client.chat.completions.create(**kwargs)
        
        return response.choices[0].message.content
    
    def get_provider_info(self) -> dict:
        """Get current provider information.
        
        Returns:
            Dict with provider and model info
        """
        return {
            "provider": self.provider,
            "model": self.model,
        }


# Global singleton instance
llm_client = LLMClient()