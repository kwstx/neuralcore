from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pydantic

class ContextBundle(pydantic.BaseModel):
    content: str
    compressed_snapshot: bytes
    fidelity: float
    metadata: Dict[str, Any]

class ContextEngineBase(ABC):
    @abstractmethod
    async def get_context(self, query: str, constraints: Dict[str, Any]) -> ContextBundle:
        """Core method to retrieve and optimize context."""
        pass

    @abstractmethod
    async def handle_mcp_fallback(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Handle Model Context Protocol fallback requests."""
        pass
