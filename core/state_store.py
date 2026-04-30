"""In-memory context store for Vera Message Engine.

Thread-safe implementation using threading.Lock for concurrent access.
Stores merchant, customer, and trigger context in memory.
"""

import threading
from datetime import datetime
from typing import Any, Optional


class StateStore:
    """Thread-safe in-memory context store.
    
    Uses a simple key-value structure with scope:context_id as the key.
    Supports versioning for idempotent updates.
    """
    
    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def set(
        self, 
        scope: str, 
        context_id: str, 
        version: int, 
        payload: dict, 
        delivered_at: str
    ) -> bool:
        """Store context with version control.
        
        Args:
            scope: Context scope (merchant, customer, trigger)
            context_id: Unique identifier for the context
            version: Version number for idempotency
            payload: The context data to store
            delivered_at: ISO timestamp when context was delivered
            
        Returns:
            True if stored/updated, False if no-op (same version already stored)
        """
        key = f"{scope}:{context_id}"
        
        with self._lock:
            existing = self._store.get(key)
            
            # Idempotent: if same version exists, no-op
            if existing and existing["version"] == version:
                return False
            
            # Only update if version is higher
            if existing and existing["version"] >= version:
                return False
            
            self._store[key] = {
                "version": version,
                "payload": payload,
                "stored_at": datetime.utcnow().isoformat() + "Z",
                "delivered_at": delivered_at
            }
            return True
    
    def get(self, scope: str, context_id: str) -> Optional[dict[str, Any]]:
        """Retrieve context by scope and ID.
        
        Args:
            scope: Context scope
            context_id: Unique identifier
            
        Returns:
            Full context entry or None if not found
        """
        key = f"{scope}:{context_id}"
        return self._store.get(key)
    
    def get_payload(self, scope: str, context_id: str) -> Optional[dict]:
        """Retrieve just the payload from context.
        
        Args:
            scope: Context scope
            context_id: Unique identifier
            
        Returns:
            Payload dict or None if not found
        """
        entry = self.get(scope, context_id)
        return entry["payload"] if entry else None
    
    def get_all_for_merchant(self, merchant_id: str) -> dict[str, Any]:
        """Get all context related to a merchant.
        
        Args:
            merchant_id: The merchant identifier
            
        Returns:
            Dict with merchant, trigger, and customer contexts
        """
        result = {
            "merchant": None,
            "trigger": None,
            "customer": None
        }
        
        with self._lock:
            for key, value in self._store.items():
                if key.startswith("merchant:") and merchant_id in key:
                    result["merchant"] = value["payload"]
                elif key.startswith("trigger:") and merchant_id in key:
                    result["trigger"] = value["payload"]
                elif key.startswith("customer:") and merchant_id in key:
                    result["customer"] = value["payload"]
        
        return result
    
    def clear(self) -> None:
        """Clear all stored context. Useful for testing."""
        with self._lock:
            self._store.clear()
    
    def keys(self) -> list[str]:
        """Get all keys in the store."""
        with self._lock:
            return list(self._store.keys())


# Global singleton instance
store = StateStore()