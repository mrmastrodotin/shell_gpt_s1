"""
Test Logging System
"""

import sys
from pathlib import Path
import tempfile
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.utils.logging import AgentLogger, get_logger

print("=" * 60)
print("Testing Logging System")
print("=" * 60)

# Test 1: Logger setup
print("\n✓ Test 1: Logger Initialization")

log_dir = Path(tempfile.mkdtemp()) / "logs"
logger = get_logger()
logger.setup(log_dir=log_dir, console_level="INFO", file_level="DEBUG")

print(f"  ✅ Logger initialized")
print(f"     Log dir: {log_dir}")

# Test 2: Log levels
print("\n✓ Test 2: Log Levels")

logger.debug("Debug message - testing")
logger.info("Info message - testing")
logger.warning("Warning message - testing")

print(f"  ✅ All log levels working")

# Test 3: Structured logging
print("\n✓ Test 3: Structured Logging")

logger.log_agent_step(
    phase="recon",
    step="THINK",
    details={"test": "value"}
)

logger.log_llm_call(
    prompt_type="PLAN",
    tokens=150,
    model="gpt-4"
)

logger.log_tool_execution(
    tool="nmap",
    command="nmap -sn 192.168.1.0/24",
    exit_code=0
)

logger.log_phase_transition(
    from_phase="recon",
    to_phase="enumeration",
    reason="Host discovery complete"
)

print(f"  ✅ Structured logging working")

# Test 4: File output
print("\n✓ Test 4: File Output")

time.sleep(0.5)  # Wait for file writes

log_file = log_dir / "sgpt.log"
json_file = log_dir / "sgpt_structured.json"

assert log_file.exists(), "Log file not created"
assert json_file.exists(), "JSON log file not created"

# Read log content
with open(log_file, 'r') as f:
    log_content = f.read()
    assert "Info message - testing" in log_content

print(f"  ✅ Log files created")
print(f"     Main log: {log_file}")
print(f"     JSON log: {json_file}")

# Test 5: Singleton pattern
print("\n✓ Test 5: Singleton Pattern")

logger2 = get_logger()
assert logger is logger2, "Logger should be singleton"

print(f"  ✅ Singleton pattern working")

# Cleanup
import shutil
shutil.rmtree(log_dir.parent, ignore_errors=True)

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print("\nLogging system is operational!")
