"""
Agent State Management
Defines the core AgentState model and related types
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from pathlib import Path
import json


class RedTeamPhase(Enum):
    """Red-team workflow phases"""
    RECON = "recon"
    RECONNAISSANCE = "recon"
    ENUMERATION = "enumeration"
    VULNERABILITY_SCAN = "vulnerability_scan"
    VULNERABILITY = "vulnerability_scan"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    REPORTING = "reporting"


@dataclass
class PhaseTransition:
    """Record of phase transitions"""
    from_phase: RedTeamPhase
    to_phase: RedTeamPhase
    timestamp: datetime
    reason: str


@dataclass
class Target:
    """Discovered target"""
    ip: str
    hostname: Optional[str] = None
    ports: list[int] = field(default_factory=list)
    services: dict[int, str] = field(default_factory=dict)
    os: Optional[str] = None
    vulnerabilities: list[str] = field(default_factory=list)


@dataclass
class Vulnerability:
    """Identified vulnerability"""
    cve_id: Optional[str]
    name: str
    severity: str  # critical, high, medium, low
    target: str
    port: Optional[int]
    description: str
    exploit_available: bool = False


@dataclass
class Command:
    """Executed command record"""
    timestamp: datetime
    command: str
    phase: RedTeamPhase
    tool_used: str
    exit_code: int
    output: str
    facts_extracted: dict
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
            "phase": self.phase.value,
            "tool_used": self.tool_used,
            "exit_code": self.exit_code,
            "output": self.output,
            "facts_extracted": self.facts_extracted
        }


@dataclass
class Failure:
    """Failed command or validation"""
    timestamp: datetime
    command: str
    reason: str
    phase: RedTeamPhase
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
            "reason": self.reason,
            "phase": self.phase.value
        }


@dataclass
class FactStore:
    """Structured knowledge base"""
    subnet: Optional[str] = None
    targets: list[Target] = field(default_factory=list)
    live_hosts: list[str] = field(default_factory=list)
    open_ports: dict[str, list[int]] = field(default_factory=dict)
    services: dict[str, dict] = field(default_factory=dict)
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    credentials: list[dict] = field(default_factory=list)
    custom_facts: dict = field(default_factory=dict)
    
    def add_host(self, ip: str):
        """Add discovered host"""
        if ip not in self.live_hosts:
            self.live_hosts.append(ip)
            
    def add_target(self, target: Target):
        """Add target with details"""
        existing = next((t for t in self.targets if t.ip == target.ip), None)
        if existing:
            # Update existing
            existing.ports = list(set(existing.ports + target.ports))
            existing.services.update(target.services)
            if target.hostname:
                existing.hostname = target.hostname
            if target.os:
                existing.os = target.os
        else:
            self.targets.append(target)
    
    def to_dict(self) -> dict:
        return {
            "subnet": self.subnet,
            "targets": [
                {
                    "ip": t.ip,
                    "hostname": t.hostname,
                    "ports": t.ports,
                    "services": t.services,
                    "os": t.os,
                    "vulnerabilities": t.vulnerabilities
                }
                for t in self.targets
            ],
            "live_hosts": self.live_hosts,
            "open_ports": self.open_ports,
            "services": self.services,
            "vulnerabilities": [
                {
                    "cve_id": v.cve_id,
                    "name": v.name,
                    "severity": v.severity,
                    "target": v.target,
                    "port": v.port,
                    "description": v.description,
                    "exploit_available": v.exploit_available
                }
                for v in self.vulnerabilities
            ],
            "credentials": self.credentials,
            "custom_facts": self.custom_facts
        }


@dataclass
class AgentState:
    """Central agent state"""
    
    # Identity
    session_id: str
    goal: str
    created_at: datetime
    
    # Phase management
    phase: RedTeamPhase = RedTeamPhase.RECON
    phase_history: list[PhaseTransition] = field(default_factory=list)
    
    # Context (populated from v1 auto-context)
    auto_context: Optional[dict] = None
    tools_available: dict[str, bool] = field(default_factory=dict)
    
    # Knowledge base
    facts: FactStore = field(default_factory=FactStore)
    
    # History
    commands_executed: list[Command] = field(default_factory=list)
    failures: list[Failure] = field(default_factory=list)
    
    # Current state
    current_objective: Optional[str] = None
    proposed_command: Optional[str] = None
    proposed_reasoning: Optional[str] = None
    waiting_for_approval: bool = False
    done: bool = False
    
    # Metadata
    total_steps: int = 0
    llm_calls: int = 0
    tokens_used: int = 0
    
    @classmethod
    def initialize(cls, session_id: str, goal: str, auto_context: dict = None) -> "AgentState":
        """Initialize new agent state"""
        return cls(
            session_id=session_id,
            goal=goal,
            created_at=datetime.now(),
            auto_context=auto_context or {}
        )
    
    def transition_phase(self, new_phase: RedTeamPhase, reason: str):
        """Transition to new phase"""
        transition = PhaseTransition(
            from_phase=self.phase,
            to_phase=new_phase,
            timestamp=datetime.now(),
            reason=reason
        )
        self.phase_history.append(transition)
        self.phase = new_phase
    
    def add_command(self, cmd: Command):
        """Record executed command"""
        self.commands_executed.append(cmd)
        self.total_steps += 1
    
    def add_failure(self, failure: Failure):
        """Record failure"""
        self.failures.append(failure)
    
    def to_dict(self) -> dict:
        """Serialize to dict for persistence"""
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "created_at": self.created_at.isoformat(),
            "phase": self.phase.value,
            "phase_history": [
                {
                    "from_phase": t.from_phase.value,
                    "to_phase": t.to_phase.value,
                    "timestamp": t.timestamp.isoformat(),
                    "reason": t.reason
                }
                for t in self.phase_history
            ],
            "auto_context": self.auto_context,
            "tools_available": self.tools_available,
            "facts": self.facts.to_dict(),
            "commands_executed": [cmd.to_dict() for cmd in self.commands_executed],
            "failures": [f.to_dict() for f in self.failures],
            "current_objective": self.current_objective,
            "proposed_command": self.proposed_command,
            "proposed_reasoning": self.proposed_reasoning,
            "waiting_for_approval": self.waiting_for_approval,
            "done": self.done,
            "total_steps": self.total_steps,
            "llm_calls": self.llm_calls,
            "tokens_used": self.tokens_used
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentState":
        """Deserialize from dict"""
        # This is simplified - full implementation would reconstruct all nested objects
        state = cls(
            session_id=data["session_id"],
            goal=data["goal"],
            created_at=datetime.fromisoformat(data["created_at"]),
            phase=RedTeamPhase(data["phase"]),
            auto_context=data.get("auto_context"),
            tools_available=data.get("tools_available", {}),
            current_objective=data.get("current_objective"),
            proposed_command=data.get("proposed_command"),
            proposed_reasoning=data.get("proposed_reasoning"),
            waiting_for_approval=data.get("waiting_for_approval", False),
            done=data.get("done", False),
            total_steps=data.get("total_steps", 0),
            llm_calls=data.get("llm_calls", 0),
            tokens_used=data.get("tokens_used", 0)
        )
        
        # Reconstruct facts
        if "facts" in data:
            facts_data = data["facts"]
            state.facts = FactStore(
                subnet=facts_data.get("subnet"),
                live_hosts=facts_data.get("live_hosts", []),
                open_ports=facts_data.get("open_ports", {}),
                services=facts_data.get("services", {}),
                credentials=facts_data.get("credentials", []),
                custom_facts=facts_data.get("custom_facts", {})
            )
            
            # Reconstruct targets
            for t_data in facts_data.get("targets", []):
                target = Target(
                    ip=t_data["ip"],
                    hostname=t_data.get("hostname"),
                    ports=t_data.get("ports", []),
                    services=t_data.get("services", {}),
                    os=t_data.get("os"),
                    vulnerabilities=t_data.get("vulnerabilities", [])
                )
                state.facts.targets.append(target)
        
                state.facts.targets.append(target)
                
        # Reconstruct commands
        if "commands_executed" in data:
            state.commands_executed = []
            for cmd_data in data["commands_executed"]:
                state.commands_executed.append(Command(
                    timestamp=datetime.fromisoformat(cmd_data["timestamp"]),
                    command=cmd_data["command"],
                    phase=RedTeamPhase(cmd_data["phase"]),
                    tool_used=cmd_data["tool_used"],
                    exit_code=cmd_data["exit_code"],
                    output=cmd_data["output"],
                    facts_extracted=cmd_data.get("facts_extracted", {})
                ))
        
        return state
