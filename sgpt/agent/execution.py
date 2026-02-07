"""
Execution Tracker
Tracks command execution status and results
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from enum import Enum


class ExecutionStatus(Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class ExecutionTracker:
    """Track command execution status and results"""
    
    def __init__(self, storage_path: Path):
        """
        Initialize execution tracker
        
        Args:
            storage_path: Base path for storing execution data
        """
        self.storage = storage_path / "executions"
        self.storage.mkdir(parents=True, exist_ok=True)
        self.pending_dir = self.storage / "pending"
        self.complete_dir = self.storage / "complete"
        self.pending_dir.mkdir(exist_ok=True)
        self.complete_dir.mkdir(exist_ok=True)
    
    def submit_command(
        self, 
        session_id: str, 
        command: str,
        tool: str = "unknown",
        phase: str = "unknown"
    ) -> str:
        """
        Submit a command for execution
        
        Args:
            session_id: Agent session ID
            command: Command to execute
            tool: Tool being used
            phase: Current phase
            
        Returns:
            Execution ID
        """
        exec_id = f"exec_{uuid.uuid4().hex[:12]}"
        
        execution_data = {
            "exec_id": exec_id,
            "session_id": session_id,
            "command": command,
            "tool": tool,
            "phase": phase,
            "status": ExecutionStatus.PENDING.value,
            "submitted_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "exit_code": None,
            "output": None,
            "error": None
        }
        
        # Save to pending
        pending_file = self.pending_dir / f"{exec_id}.json"
        with open(pending_file, 'w') as f:
            json.dump(execution_data, f, indent=2)
        
        return exec_id
    
    def mark_running(self, exec_id: str):
        """Mark execution as running"""
        pending_file = self.pending_dir / f"{exec_id}.json"
        
        if not pending_file.exists():
            raise ValueError(f"Execution {exec_id} not found")
        
        with open(pending_file, 'r') as f:
            data = json.load(f)
        
        data["status"] = ExecutionStatus.RUNNING.value
        data["started_at"] = datetime.now().isoformat()
        
        with open(pending_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_result(
        self,
        exec_id: str,
        exit_code: int,
        output: str,
        error: str = None
    ):
        """
        Save execution result
        
        Args:
            exec_id: Execution ID
            exit_code: Command exit code
            output: Command output (stdout)
            error: Error output (stderr)
        """
        pending_file = self.pending_dir / f"{exec_id}.json"
        
        if not pending_file.exists():
            raise ValueError(f"Execution {exec_id} not found")
        
        with open(pending_file, 'r') as f:
            data = json.load(f)
        
        data["status"] = ExecutionStatus.COMPLETE.value if exit_code == 0 else ExecutionStatus.FAILED.value
        data["completed_at"] = datetime.now().isoformat()
        data["exit_code"] = exit_code
        data["output"] = output
        data["error"] = error
        
        # Move to complete
        complete_file = self.complete_dir / f"{exec_id}.json"
        with open(complete_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Remove from pending
        pending_file.unlink()
    
    def get_status(self, exec_id: str) -> Optional[Dict]:
        """
        Get execution status
        
        Returns:
            Execution data dict or None if not found
        """
        # Check pending
        pending_file = self.pending_dir / f"{exec_id}.json"
        if pending_file.exists():
            with open(pending_file, 'r') as f:
                return json.load(f)
        
        # Check complete
        complete_file = self.complete_dir / f"{exec_id}.json"
        if complete_file.exists():
            with open(complete_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def get_pending(self, session_id: str = None) -> list[Dict]:
        """
        Get all pending executions
        
        Args:
            session_id: Optional filter by session
            
        Returns:
            List of pending execution data
        """
        pending = []
        
        for file in self.pending_dir.glob("*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                if session_id is None or data["session_id"] == session_id:
                    pending.append(data)
        
        return pending
    
    def get_session_executions(self, session_id: str) -> list[Dict]:
        """
        Get all executions for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of all execution data (pending + complete)
        """
        executions = []
        
        # Get pending
        for file in self.pending_dir.glob("*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                if data["session_id"] == session_id:
                    executions.append(data)
        
        # Get complete
        for file in self.complete_dir.glob("*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                if data["session_id"] == session_id:
                    executions.append(data)
        
        # Sort by submission time
        executions.sort(key=lambda x: x["submitted_at"])
        
        return executions
    
    def cleanup_session(self, session_id: str):
        """Clean up all executions for a session"""
        for file in self.pending_dir.glob("*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                if data["session_id"] == session_id:
                    file.unlink()
        
        for file in self.complete_dir.glob("*.json"):
            with open(file, 'r') as f:
                data = json.load(f)
                if data["session_id"] == session_id:
                    file.unlink()
