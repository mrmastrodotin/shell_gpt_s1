"""
Agent Resume Module
Handle session resumption with context restoration
"""

from sgpt.agent.loop import Agent
from sgpt.agent.state import AgentState
from pathlib import Path
from typing import Dict, Any


class AgentResume:
    """Handle agent session resumption"""
    
    @staticmethod
    def get_resume_context(state: AgentState) -> Dict[str, Any]:
        """
        Build resume context from saved state
        
        Returns summary of:
        - Session info (ID, goal, phase, created_at)
        - Progress (commands executed, facts discovered)
        - Current objective
        - Next steps suggestion
        """
        context = {
            'session_id': state.session_id,
            'goal': state.goal,
            'phase': state.phase.value,
            'created_at': state.created_at,
            'commands_count': len(state.commands_executed),
            'done': state.done
        }
        
        # Facts summary
        context['facts'] = {
            'live_hosts': len(state.facts.live_hosts),
            'open_ports': len(state.facts.open_ports),
            'vulnerabilities': len(state.facts.vulnerabilities),
            'credentials': len(state.facts.credentials),
            'targets': len(state.facts.targets)
        }
        
        # Last command
        if state.commands_executed:
            last_cmd = state.commands_executed[-1]
            context['last_command'] = {
                'command': last_cmd.command,
                'tool': last_cmd.tool_used,
                'timestamp': last_cmd.timestamp.isoformat() if hasattr(last_cmd.timestamp, 'isoformat') else last_cmd.timestamp
            }
        
        # Phase history
        if state.phase_history:
            context['phase_transitions'] = len(state.phase_history)
        
        return context
    
    @staticmethod
    def print_resume_summary(context: Dict[str, Any]):
        """Print formatted resume summary"""
        print("\n" + "=" * 60)
        print("📋 RESUMING AGENT SESSION")
        print("=" * 60)
        
        print(f"\n🆔 Session: {context['session_id']}")
        print(f"🎯 Goal: {context['goal']}")
        print(f"📍 Current Phase: {context['phase'].upper()}")
        print(f"⏰ Started: {context['created_at']}")
        
        print(f"\n📊 Progress:")
        print(f"   Commands Executed: {context['commands_count']}")
        print(f"   Hosts Discovered: {context['facts']['live_hosts']}")
        print(f"   Open Ports: {context['facts']['open_ports']}")
        print(f"   Vulnerabilities: {context['facts']['vulnerabilities']}")
        print(f"   Targets Identified: {context['facts']['targets']}")
        
        if 'last_command' in context:
            print(f"\n🔧 Last Command:")
            print(f"   Tool: {context['last_command'].get('tool', 'unknown')}")
            print(f"   Command: {context['last_command'].get('command', 'N/A')[:60]}...")
        
        if context.get('phase_transitions'):
            print(f"\n🔄 Phase Transitions: {context['phase_transitions']}")
        
        if context['done']:
            print(f"\n✅ Status: GOAL SATISFIED")
        else:
            print(f"\n⏳ Status: IN PROGRESS - Resuming from last checkpoint")
        
        print("\n" + "=" * 60 + "\n")
    
    @staticmethod
    def validate_resume(state: AgentState) -> tuple[bool, str]:
        """
        Validate that session can be resumed
        
        Returns:
            (can_resume, reason)
        """
        # Check if already done
        if state.done:
            return False, "Session already completed (goal satisfied)"
        
        # Check if session is too old (optional safety check)
        from datetime import datetime, timedelta
        
        if isinstance(state.created_at, str):
            created = datetime.fromisoformat(state.created_at)
        else:
            created = state.created_at
            
        age = datetime.now() - created
        
        if age > timedelta(days=30):
            return True, f"Warning: Session is {age.days} days old"
        
        # Check for corruption indicators
        if not state.session_id or not state.goal:
            return False, "Session state corrupted (missing required fields)"
        
        return True, "Session is valid and can be resumed"
    
    @staticmethod
    async def resume_and_run(
        session_id: str,
        storage_path: str = None,
        llm_provider=None,
        tool_registry=None,
        verbose: bool = True
    ) -> Agent:
        """
        Resume session and continue agent loop
        
        Args:
            session_id: Session ID to resume
            storage_path: Storage path
            llm_provider: LLM provider
            tool_registry: Tool registry
            verbose: Print resume summary
            
        Returns:
            Agent instance
        """
        # Resume agent
        agent = Agent.resume_from_session(
            session_id=session_id,
            storage_path=storage_path,
            llm_provider=llm_provider,
            tool_registry=tool_registry
        )
        
        # Validate
        can_resume, reason = AgentResume.validate_resume(agent.state)
        
        if not can_resume:
            raise ValueError(f"Cannot resume session: {reason}")
        
        # Get context
        context = AgentResume.get_resume_context(agent.state)
        
        # Print summary
        if verbose:
            AgentResume.print_resume_summary(context)
            
            if "Warning" in reason:
                print(f"⚠️  {reason}\n")
        
        # Continue agent loop
        print("🚀 Continuing agent execution...\n")
        await agent.run()
        
        return agent
