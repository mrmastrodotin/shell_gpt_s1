"""
Test Configuration System
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.config.manager import ConfigManager, LLMConfig, get_config

print("=" * 60)
print("Testing Configuration System")
print("=" * 60)

# Test 1: Default configuration
print("\n✓ Test 1: Default Configuration")

manager = ConfigManager()
config = manager.load()

assert config.llm.interface == "openai"
assert config.llm.temperature == 0.7
assert config.execution.timeout == 300
assert config.logging.console_level == "INFO"

print(f"  ✅ Default config loaded")
print(f"     LLM: {config.llm.interface}")
print(f"     Temperature: {config.llm.temperature}")
print(f"     Timeout: {config.execution.timeout}")

# Test 2: YAML configuration
print("\n✓ Test 2: YAML Configuration")

temp_config = Path(tempfile.mktemp(suffix=".yaml"))

# Create custom config
custom_config = """
llm:
  interface: gemini
  model: gemini-pro
  temperature: 0.5

execution:
  timeout: 600

logging:
  console_level: DEBUG
"""

with open(temp_config, 'w') as f:
    f.write(custom_config)

# Load custom config
manager2 = ConfigManager()
config2 = manager2.load(temp_config)

assert config2.llm.interface == "gemini"
assert config2.llm.model == "gemini-pro"
assert config2.llm.temperature == 0.5
assert config2.execution.timeout == 600
assert config2.logging.console_level == "DEBUG"

print(f"  ✅ YAML config loaded")
print(f"     LLM: {config2.llm.interface} ({config2.llm.model})")
print(f"     Timeout: {config2.execution.timeout}")

# Test 3: Environment variable override
print("\n✓ Test 3: Environment Variables")

os.environ['SGPT_LLM_INTERFACE'] = 'ollama'
os.environ['SGPT_LLM_TEMPERATURE'] = '0.9'
os.environ['SGPT_LOG_LEVEL'] = 'WARNING'

manager3 = ConfigManager()
config3 = manager3.load(temp_config)

assert config3.llm.interface == "ollama"  # ENV overrides YAML
assert config3.llm.temperature == 0.9
assert config3.logging.console_level == "WARNING"

print(f"  ✅ Environment overrides working")
print(f"     LLM: {config3.llm.interface}")
print(f"     Temperature: {config3.llm.temperature}")

# Test 4: Save configuration
print("\n✓ Test 4: Save Configuration")

save_path = Path(tempfile.mktemp(suffix=".yaml"))
manager3.save(save_path)

assert save_path.exists()

print(f"  ✅ Config saved to: {save_path}")

# Test 5: Global config
print("\n✓ Test 5: Global Config Access")

global_config = get_config()
assert global_config is not None

print(f"  ✅ Global config accessible")

# Cleanup
temp_config.unlink()
save_path.unlink()
del os.environ['SGPT_LLM_INTERFACE']
del os.environ['SGPT_LLM_TEMPERATURE']
del os.environ['SGPT_LOG_LEVEL']

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print("\nConfiguration system is operational!")
