"""
Test real execution system
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.agent.execution import ExecutionTracker, ExecutionStatus

print("=" * 60)
print("Testing Real Execution System")
print("=" * 60)

# Test 1: Initialize tracker
print("\n✓ Test 1: Initialize ExecutionTracker")
storage = Path("c:/temp/sgpt_test")
tracker = ExecutionTracker(storage)
print(f"  ✅ Tracker created at {storage}")

# Test 2: Submit command
print("\n✓ Test 2: Submit Command")
exec_id = tracker.submit_command(
    session_id="test_session",
    command="nmap -sn 192.168.1.0/24",
    tool="nmap",
    phase="recon"
)
print(f"  ✅ Execution ID: {exec_id}")

# Test 3: Get status
print("\n✓ Test 3: Get Status")
status = tracker.get_status(exec_id)
assert status["status"] == ExecutionStatus.PENDING.value
assert status["command"] == "nmap -sn 192.168.1.0/24"
print(f"  ✅ Status: {status['status']}")
print(f"     Command: {status['command']}")

# Test 4: Mark running
print("\n✓ Test 4: Mark Running")
tracker.mark_running(exec_id)
status = tracker.get_status(exec_id)
assert status["status"] == ExecutionStatus.RUNNING.value
print(f"  ✅ Status: {status['status']}")

# Test 5: Save result
print("\n✓ Test 5: Save Result")
output = "Host 192.168.1.1 is up\nHost 192.168.1.10 is up"
tracker.save_result(exec_id, 0, output)
status = tracker.get_status(exec_id)
assert status["status"] == ExecutionStatus.COMPLETE.value
assert status["exit_code"] == 0
print(f"  ✅ Status: {status['status']}")
print(f"     Exit code: {status['exit_code']}")

# Test 6: Get session executions
print("\n✓ Test 6: Get Session Executions")
executions = tracker.get_session_executions("test_session")
assert len(executions) == 1
print(f"  ✅ Found {len(executions)} execution(s)")

# Cleanup
print("\n✓ Cleanup")
tracker.cleanup_session("test_session")
print("  ✅ Session cleaned up")

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print("\nReal execution system is operational!")
