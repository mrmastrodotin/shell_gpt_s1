"""
Tool Registry System
Manages available tools and command generation
"""

from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional
from sgpt.agent.state import RedTeamPhase


class ToolCategory(Enum):
    """Tool categories"""
    DISCOVERY = "discovery"
    ENUMERATION = "enumeration"
    VULNERABILITY = "vulnerability"
    WEB = "web"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    SCRIPTING = "scripting"


@dataclass
class ToolSpec:
    """Tool specification and metadata"""
    name: str
    binary: str  # Actual command binary
    category: ToolCategory
    phases: list[RedTeamPhase]
    requires_root: bool
    destructive: bool
    network_active: bool
    description: str
    safe_flags: list[str]  # Only these flags are allowed


class BaseTool(ABC):
    """Base class for all tools"""
    
    spec: ToolSpec
    
    @abstractmethod
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """
        Generate command for given intent
        
        Args:
            intent: What the agent wants to do (e.g., "host_discovery")
            context: Auto-context from system
            facts: Known facts from agent state
        
        Returns:
            Command string
        """
        pass
    
    @abstractmethod  
    def parse_output(self, output: str) -> dict:
        """
        Parse tool output to extract facts
        
        Args:
            output: Raw command output
        
        Returns:
            Dict of extracted facts
        """
        pass
    
    def validate_flags(self, flags: list[str]) -> bool:
        """Check if flags are safe"""
        return all(flag in self.spec.safe_flags for flag in flags)


class ToolRegistry:
    """Central registry of available tools"""
    
    def __init__(self):
        self.tools: dict[str, BaseTool] = {}
        self._loaded = False
    
    def load_tools(self):
        """Load all available tools"""
        if self._loaded:
            return
        
        # Import and register tools
        tools_to_load = [
            ("sgpt.tools.specs.nmap", "NmapTool"),
            ("sgpt.tools.specs.curl", "CurlTool"),
            ("sgpt.tools.specs.python_script", "PythonScriptTool"),
            ("sgpt.tools.specs.gobuster", "GobusterTool"),
            ("sgpt.tools.specs.nikto", "NiktoTool"),
        ]
        
        for module_path, class_name in tools_to_load:
            try:
                module = __import__(module_path, fromlist=[class_name])
                tool_class = getattr(module, class_name)
                self.register(tool_class())
            except ImportError as e:
                pass  # Tool module not available
            except Exception as e:
                print(f"Warning: Failed to load {class_name}: {e}")
        
        self._loaded = True
    
    def register(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.spec.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def get_for_phase(self, phase: RedTeamPhase) -> list[ToolSpec]:
        """Get all tools available for a phase"""
        return [
            tool.spec
            for tool in self.tools.values()
            if phase in tool.spec.phases
        ]
    
    def get_for_category(self, category: ToolCategory) -> list[ToolSpec]:
        """Get tools by category"""
        return [
            tool.spec
            for tool in self.tools.values()
            if tool.spec.category == category
        ]
    
    def list_all(self) -> list[str]:
        """List all registered tool names"""
        return list(self.tools.keys())
