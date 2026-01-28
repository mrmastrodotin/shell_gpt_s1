from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class SystemContext:
    os: str
    distro: str
    kernel: str
    arch: str
    privilege: str
    shell: str
    user: str

@dataclass
class NetworkContext:
    interface: str
    ip: str
    subnet: str
    default_route: str
    environment: str

@dataclass
class RuntimeContext:
    cwd: str
    # Add other runtime info if needed (e.g. active virtualenv)

@dataclass
class CommandRecord:
    command: str
    summary: str
    timestamp: datetime

@dataclass
class SessionMemory:
    started_at: datetime
    commands: List[CommandRecord] = field(default_factory=list)

@dataclass
class BehaviorRules:
    verbosity: str = "low"
    no_questions: bool = True
    no_suggestions: bool = True
    no_fluff: bool = True
    no_comparisons: bool = True

@dataclass
class AutoContext:
    system: SystemContext
    network: NetworkContext
    tools: Dict[str, bool]
    runtime: RuntimeContext
    behavior: BehaviorRules
    session: SessionMemory
