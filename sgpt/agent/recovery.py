"""
State Recovery System
Handle state corruption and auto-save
"""

from sgpt.agent.state import AgentState
from sgpt.agent.persistence import AgentPersistence
from pathlib import Path
import json
import shutil
from datetime import datetime
from typing import Optional


class StateRecovery:
    """Handle state recovery and backups"""
    
    def __init__(self, persistence: AgentPersistence):
        self.persistence = persistence
        self.backup_dir = persistence.storage_path / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, state: AgentState, label: str = "auto"):
        """
        Create state backup
        
        Args:
            state: Agent state to backup
            label: Backup label (auto, manual, pre-command, etc.)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{state.session_id}_{label}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
            
            # Keep only last 10 backups per session
            self._cleanup_old_backups(state.session_id, keep=10)
            
        except Exception as e:
            print(f"⚠️  Backup creation failed: {e}")
    
    def _cleanup_old_backups(self, session_id: str, keep: int = 10):
        """Keep only the most recent backups"""
        backups = sorted(
            [f for f in self.backup_dir.glob(f"{session_id}_*.json")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Delete old backups
        for backup in backups[keep:]:
            try:
                backup.unlink()
            except:
                pass
    
    def restore_from_backup(self, session_id: str, backup_name: str = None) -> Optional[AgentState]:
        """
        Restore state from backup
        
        Args:
            session_id: Session ID
            backup_name: Specific backup to restore, or None for latest
            
        Returns:
            Restored AgentState or None
        """
        if backup_name:
            backup_path = self.backup_dir / backup_name
        else:
            # Find latest backup
            backups = sorted(
                [f for f in self.backup_dir.glob(f"{session_id}_*.json")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            if not backups:
                print(f"❌ No backups found for session {session_id}")
                return None
            
            backup_path = backups[0]
        
        try:
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            state = AgentState.from_dict(data)
            print(f"✅ Restored from backup: {backup_path.name}")
            return state
            
        except Exception as e:
            print(f"❌ Backup restore failed: {e}")
            return None
    
    def validate_state(self, state: AgentState) -> bool:
        """
        Validate state integrity
        
        Returns:
            True if state is valid
        """
        try:
            # Check required fields
            assert state.session_id, "Missing session_id"
            assert state.goal, "Missing goal"
            assert state.created_at, "Missing created_at"
            assert state.phase, "Missing phase"
            assert state.facts, "Missing facts"
            
            # Check types
            assert isinstance(state.commands_executed, list)
            assert isinstance(state.failures, list)
            
            return True
            
        except AssertionError as e:
            print(f"⚠️  State validation failed: {e}")
            return False
    
    def auto_save(self, state: AgentState):
        """
        Auto-save state with backup
        
        Called after each command execution
        """
        try:
            # Create backup first
            self.create_backup(state, label="auto")
            
            # Save current state
            self.persistence.save_state(state)
            
        except Exception as e:
            print(f"⚠️  Auto-save failed: {e}")
    
    def recover_or_create(self, session_id: str, goal: str = None) -> AgentState:
        """
        Try to recover state, or create new if recovery fails
        
        Args:
            session_id: Session ID
            goal: Goal for new session if recovery fails
            
        Returns:
            Recovered or new AgentState
        """
        # Try to load existing state
        try:
            state = self.persistence.load_state(session_id)
            
            # Validate
            if self.validate_state(state):
                print(f"✅ Recovered session: {session_id}")
                return state
            else:
                print(f"⚠️  State corrupted, attempting backup restore...")
                
        except FileNotFoundError:
            print(f"ℹ️  No existing session found")
        except Exception as e:
            print(f"⚠️  State load failed: {e}")
        
        # Try backup restore
        backup_state = self.restore_from_backup(session_id)
        if backup_state and self.validate_state(backup_state):
            return backup_state
        
        # Create new state
        print(f"🆕 Creating new session: {session_id}")
        return AgentState.initialize(
            session_id=session_id,
            goal=goal or "New session"
        )
