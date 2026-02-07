"""
State Persistence
Save and load agent state
"""

from pathlib import Path
import json
from typing import Optional
from sgpt.agent.state import AgentState


class AgentPersistence:
    """Handle agent state persistence"""
    
    def __init__(self, config_dir: Path):
        self.agents_dir = config_dir / "agents"
        self.storage_path = config_dir
        self.agents_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session_dir(self, session_id: str) -> Path:
        """Get directory for session"""
        session_dir = self.agents_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_state(self, state: AgentState):
        """Save agent state"""
        session_dir = self.get_session_dir(state.session_id)
        state_file = session_dir / "state.json"
        
        with open(state_file, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)
    
    def load_state(self, session_id: str) -> Optional[AgentState]:
        """Load agent state"""
        session_dir = self.get_session_dir(session_id)
        state_file = session_dir / "state.json"
        
        if not state_file.exists():
            return None
        
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        return AgentState.from_dict(data)
    
    def list_sessions(self) -> list[str]:
        """List all agent sessions"""
        if not self.agents_dir.exists():
            return []
        
        return [d.name for d in self.agents_dir.iterdir() if d.is_dir()]
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return (self.agents_dir / session_id).exists()
