import os
import json
import tempfile
from datetime import datetime
from dataclasses import asdict
from typing import Optional
from sgpt.context.models import SessionMemory, CommandRecord

def get_session_file_path() -> str:
    # Key session by Parent Process ID (Shell PID)
    # This scopes context to the current terminal window/tab.
    try:
        ppid = os.getppid()
    except AttributeError:
        # Fallback for systems without getppid
        ppid = os.getpid()
        
    filename = f"sgpt_session_{ppid}.json"
    return os.path.join(tempfile.gettempdir(), filename)

def get_context_file_path() -> str:
    """Returns the path for the auto-context file (scoped to session/PID)."""
    session_path = get_session_file_path()
    return session_path.replace("sgpt_session_", "sgpt_context_")

def load_session() -> SessionMemory:
    path = get_session_file_path()
    if not os.path.exists(path):
        return SessionMemory(started_at=datetime.now(), commands=[])
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
            # Reconstruct objects
            # Handle datetime parsing if needed, usually isoformat in JSON
            started = datetime.fromisoformat(data["started_at"])
            commands = []
            for cmd in data.get("commands", []):
                commands.append(CommandRecord(
                    command=cmd["command"],
                    summary=cmd["summary"],
                    timestamp=datetime.fromisoformat(cmd["timestamp"])
                ))
            return SessionMemory(started_at=started, commands=commands)
    except Exception:
        return SessionMemory(started_at=datetime.now(), commands=[])

def save_session(session: SessionMemory) -> None:
    path = get_session_file_path()
    data = asdict(session)
    # custom serializer for datetime
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
        
    with open(path, "w") as f:
        json.dump(data, f, default=json_serial, indent=2)

def add_command_record(command: str, summary: str) -> None:
    session = load_session()
    record = CommandRecord(
        command=command,
        summary=summary,
        timestamp=datetime.now()
    )
    session.commands.append(record)
    save_session(session)

def clear_session() -> None:
    path = get_session_file_path()
    if os.path.exists(path):
        os.remove(path)
