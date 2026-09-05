# Tools — MCP-Style Capability Declarations

"""
Tool/capability definitions for agent.
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass


@dataclass
class Tool:
    """Tool definition."""
    name: str
    description: str
    parameters: Dict
    handler: Callable
    
    def execute(self, **kwargs) -> Any:
        """Execute tool."""
        return self.handler(**kwargs)


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        """Register tool."""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Tool:
        """Get tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all tool names."""
        return list(self.tools.keys())
    
    def execute(self, name: str, **kwargs) -> Any:
        """Execute tool by name."""
        tool = self.get(name)
        if tool:
            return tool.execute(**kwargs)
        raise ValueError(f"Unknown tool: {name}")


# Example: Register tools
def create_tools() -> ToolRegistry:
    """Create standard toolset."""
    registry = ToolRegistry()
    
    # Navigation tools
    registry.register(Tool(
        name="move_to",
        description="Move to position",
        parameters={"position": {"type": "array", "description": "[x, y, z]"}},
        handler=lambda position: {"status": "moved", "to": position}
    ))
    
    # Perception tools
    registry.register(Tool(
        name="scan",
        description="Scan environment",
        parameters={},
        handler=lambda: {"objects": [], "position": [0, 0, 0]}
    ))
    
    # Communication
    registry.register(Tool(
        name="say",
        description="Speak to human",
        parameters={"message": {"type": "string"}},
        handler=lambda message: {"spoken": message}
    ))
    
    return registry


# Singleton
tools = create_tools()
