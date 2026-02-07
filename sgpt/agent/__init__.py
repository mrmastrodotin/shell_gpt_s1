"""
ShellGPT v2 - Red-Team Automation Agent
Agent Core Module
"""

from sgpt.agent.state import AgentState, RedTeamPhase
from sgpt.agent.loop import Agent
from sgpt.agent.persistence import AgentPersistence

__all__ = ["AgentState", "RedTeamPhase", "Agent", "AgentPersistence"]
