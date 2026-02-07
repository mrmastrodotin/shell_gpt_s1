"""
Test Error Recovery System
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.agent.retry import RetryHandler, with_retry
from sgpt.agent.state import AgentState
from sgpt.agent.persistence import AgentPersistence
from sgpt.agent.recovery import StateRecovery

print("=" * 60)
print("Testing Error Recovery System")
print("=" * 60)

# Test 1: Retry logic
print("\n✓ Test 1: Retry with Exponential Backoff")

attempt_count = 0

def flaky_function():
    global attempt_count
    attempt_count += 1
    
    if attempt_count < 3:
        raise Exception(f"Attempt {attempt_count} failed!")
    
    return "Success!"

result = RetryHandler.retry_sync(flaky_function, max_attempts=3, base_delay=0.1)
assert result == "Success!"
print(f"  ✅ Function succeeded on attempt {attempt_count}")

# Test 2: Async retry
print("\n✓ Test 2: Async Retry")

async def test_async_retry():
    global attempt_count
    attempt_count = 0
    
    async def async_flaky():
        global attempt_count
        attempt_count += 1
        
        if attempt_count < 2:
            raise Exception("Async failure!")
        
        return "Async success!"
    
    result = await RetryHandler.retry_async(async_flaky, max_attempts=3, base_delay=0.1)
    assert result == "Async success!"
    print(f"  ✅ Async succeeded on attempt {attempt_count}")

asyncio.run(test_async_retry())

# Test 3: Decorator
print("\n✓ Test 3: Retry Decorator")

call_count = 0

@with_retry(max_attempts=3, base_delay=0.1)
def decorated_function():
    global call_count
    call_count += 1
    
    if call_count < 2:
        raise ValueError("Decorated failure!")
    
    return "Decorated success!"

call_count = 0
result = decorated_function()
assert result == "Decorated success!"
print(f"  ✅ Decorated function succeeded")

# Test 4: State Recovery
print("\n✓ Test 4: State Backup & Recovery")

storage_path = Path("c:/temp/sgpt_recovery_test")
persistence = AgentPersistence(storage_path)
recovery = StateRecovery(persistence)

state = AgentState.initialize("test_recovery", "Test recovery system")
state.facts.live_hosts.append("192.168.1.1")

# Create backup
recovery.create_backup(state, "test")
print(f"  ✅ Created backup")

# Validate
is_valid = recovery.validate_state(state)
assert is_valid
print(f"  ✅ State validation passed")

# Restore
restored = recovery.restore_from_backup("test_recovery")
assert restored is not None
assert restored.session_id == "test_recovery"
print(f"  ✅ Restored from backup")

# Test 5: Auto-save
print("\n✓ Test 5: Auto-Save")

recovery.auto_save(state)
print(f"  ✅ Auto-save completed")

# Cleanup
import shutil
shutil.rmtree(storage_path, ignore_errors=True)

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print("\nError recovery system is operational!")
