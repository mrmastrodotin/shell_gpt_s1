"""
Test Agent Resume Functionality
"""

import sys
from pathlib import Path
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.agent.state import AgentState, Command, RedTeamPhase
from sgpt.agent.persistence import AgentPersistence
from sgpt.agent.loop import Agent
from sgpt.agent.resume import AgentResume

print("=" * 60)
print("Testing Agent Resume Functionality")
print("=" * 60)

# Test 1: Create and save session
print("\n✓ Test 1: Create Session State")

storage_path = Path(tempfile.mkdtemp()) / "agent_sessions"
persistence = AgentPersistence(storage_path)

state = AgentState.initialize("test_resume_session", "Test resume functionality")
state.facts.live_hosts.append("192.168.1.1")
state.facts.live_hosts.append("192.168.1.10")
from datetime import datetime
state.commands_executed.append(Command(
    command='nmap -sn 192.168.1.0/24',
    tool_used='nmap',
    timestamp=datetime.now(),
    exit_code=0,
    output='Scan output',
    phase=RedTeamPhase.RECON,
    facts_extracted={}
))

persistence.save_state(state)
print(f"  ✅ Session created and saved")

# Test 2: Resume from session
print("\n✓ Test 2: Resume Agent from Session")

agent = Agent.resume_from_session(
    session_id="test_resume_session",
    storage_path=storage_path
)

assert agent.state.session_id == "test_resume_session"
assert agent.state.goal == "Test resume functionality"
assert len(agent.state.facts.live_hosts) == 2
assert len(agent.state.commands_executed) == 1

print(f"  ✅ Agent resumed successfully")
print(f"     Session ID: {agent.state.session_id}")
print(f"     Goal: {agent.state.goal}")
print(f"     Hosts: {len(agent.state.facts.live_hosts)}")
print(f"     Commands: {len(agent.state.commands_executed)}")

# Test 3: Get resume context
print("\n✓ Test 3: Get Resume Context")

context = AgentResume.get_resume_context(agent.state)

assert context['session_id'] == "test_resume_session"
assert context['goal'] == "Test resume functionality"
assert context['facts']['live_hosts'] == 2
assert context['commands_count'] == 1
assert 'last_command' in context

print(f"  ✅ Resume context generated")
print(f"     Facts summary: {context['facts']}")
print(f"     Last command: {context['last_command']['tool']}")

# Test 4: Validate resume
print("\n✓ Test 4: Validate Resume")

can_resume, reason = AgentResume.validate_resume(agent.state)

assert can_resume == True
print(f"  ✅ Validation passed")
print(f"     Reason: {reason}")

# Test 5: Cannot resume completed session
print("\n✓ Test 5: Reject Completed Session")

completed_state = AgentState.initialize("completed_session", "Already done")
completed_state.done = True

can_resume, reason = AgentResume.validate_resume(completed_state)

assert can_resume == False
assert "completed" in reason.lower()
print(f"  ✅ Completed session rejected")
print(f"     Reason: {reason}")

# Test 6: Print resume summary
print("\n✓ Test 6: Resume Summary Display")

AgentResume.print_resume_summary(context)
print(f"  ✅ Summary displayed")

# Cleanup
import shutil
shutil.rmtree(storage_path.parent, ignore_errors=True)

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print("\nAgent resume functionality is operational!")
print(f"\nUsage:")
print(f"  sgpt agent resume SESSION_ID")
