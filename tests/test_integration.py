"""
Integration Test Suite for ShellGPT v2 Agent
Tests the complete agent workflow end-to-end
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import sgpt
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import tempfile

# Import v2 components
from sgpt.agent.state import AgentState, RedTeamPhase
from sgpt.agent.loop import Agent
from sgpt.agent.persistence import AgentPersistence
from sgpt.tools.registry import ToolRegistry


async def test_agent_initialization():
    """Test 1: Agent initialization and state creation"""
    print("\n" + "="*60)
    print("TEST 1: Agent Initialization")
    print("="*60)
    
    # Create temp directory for state
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        
        # Initialize components
        state = AgentState.initialize(
            session_id="test_001",
            goal="Test network enumeration"
        )
        
        persistence = AgentPersistence(storage_path)
        registry = ToolRegistry()
        registry.load_tools()
        
        agent = Agent(
            state=state,
            persistence=persistence,
            llm_provider=None,  # No LLM for basic test
            tool_registry=registry
        )
        
        print(f"✅ Agent created with session: {state.session_id}")
        print(f"✅ Goal: {state.goal}")
        print(f"✅ Phase: {state.phase.value}")
        print(f"✅ Tools loaded: {len(registry._tools)}")
        
        # Save state
        persistence.save_state(state)
        
        # Load state back
        loaded_state = persistence.load_state("test_001")
        assert loaded_state.goal == state.goal
        
        print(f"✅ State persistence working")
        
        return True


async def test_tool_availability():
    """Test 2: Tool availability detection"""
    print("\n" + "="*60)
    print("TEST 2: Tool Availability Detection")
    print("="*60)
    
    from sgpt.tools.availability import ToolAvailabilityChecker
    
    registry = ToolRegistry()
    registry.load_tools()
    
    availability = ToolAvailabilityChecker.check_all(registry)
    
    print(f"✅ Checked {len(availability)} tools")
    
    for binary, is_available in availability.items():
        status = "✅ FOUND" if is_available else "❌ MISSING"
        print(f"   {binary:15s} {status}")
    
    return True


async def test_tool_command_generation():
    """Test 3: Tool command generation"""
    print("\n" + "="*60)
    print("TEST 3: Tool Command Generation")
    print("="*60)
    
    registry = ToolRegistry()
    registry.load_tools()
    
    # Test nmap tool
    nmap_tool = registry.get("nmap")
    if nmap_tool:
        context = {"network": {"subnet": "192.168.1.0/24"}}
        facts = {}
        
        command = nmap_tool.generate_command(
            intent="host_discovery",
            context=context,
            facts=facts
        )
        
        print(f"✅ Nmap host discovery: {command}")
        assert "nmap" in command
        assert "192.168.1.0/24" in command
    
    # Test curl tool
    curl_tool = registry.get("curl")
    if curl_tool:
        facts = {
            "targets": [{
                "ip": "192.168.1.10",
                "services": {"80": "Apache httpd 2.4"}
            }]
        }
        
        command = curl_tool.generate_command(
            intent="web_probe",
            context={},
            facts=facts
        )
        
        print(f"✅ Curl web probe: {command}")
        assert "curl" in command
    
    return True


async def test_safety_validator():
    """Test 4: Safety validation"""
    print("\n" + "="*60)
    print("TEST 4: Safety Validation")
    print("="*60)
    
    from sgpt.tools.safety import SafetyValidator
    
    # Test safe command
    safe_cmd = "nmap -sn 192.168.1.0/24"
    is_safe, reason = SafetyValidator.validate(safe_cmd)
    assert is_safe
    print(f"✅ Safe command passed: {safe_cmd}")
    
    # Test destructive command
    destructive_cmd = "rm -rf /important/data"
    is_safe, reason = SafetyValidator.validate(destructive_cmd)
    assert not is_safe
    print(f"✅ Destructive command blocked: {destructive_cmd}")
    print(f"   Reason: {reason}")
    
    # Test privilege escalation
    priv_cmd = "sudo rm /etc/passwd"
    is_safe, reason = SafetyValidator.validate(priv_cmd)
    assert not is_safe
    print(f"✅ Privilege escalation blocked: {priv_cmd}")
    print(f"   Reason: {reason}")
    
    return True


async def test_fact_extraction():
    """Test 5: Fact extraction from tool output"""
    print("\n" + "="*60)
    print("TEST 5: Fact Extraction")
    print("="*60)
    
    registry = ToolRegistry()
    registry.load_tools()
    
    nmap_tool = registry.get("nmap")
    if nmap_tool:
        # Simulate nmap output
        sample_output = """
Starting Nmap 7.80 ( https://nmap.org )
Nmap scan report for 192.168.1.1
Host is up (0.0010s latency).
Nmap scan report for 192.168.1.10
Host is up (0.0020s latency).
Nmap done: 256 IP addresses (2 hosts up) scanned in 5.67 seconds
"""
        
        facts = nmap_tool.parse_output(sample_output)
        
        print(f"✅ Extracted hosts: {facts.get('hosts', [])}")
        assert len(facts.get('hosts', [])) >= 2
    
    return True


async def test_agent_observe_phase():
    """Test 6: Agent observation phase"""
    print("\n" + "="*60)
    print("TEST 6: Agent Observation")
    print("="*60)
    
    state = AgentState.initialize(
        session_id="test_observe",
        goal="Enumerate network"
    )
    
    registry = ToolRegistry()
    registry.load_tools()
    
    agent = Agent(
        state=state,
        persistence=AgentPersistence(Path(tempfile.gettempdir())),
        llm_provider=None,
        tool_registry=registry
    )
    
    observation = agent.observe()
    
    print(f"✅ Observation created")
    print(f"   Goal: {observation['goal']}")
    print(f"   Phase: {observation['phase']}")
    print(f"   Total commands: {observation['total_commands']}")
    
    assert observation['goal'] == state.goal
    assert observation['phase'] == state.phase.value
    
    return True


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "🧪 " * 20)
    print("ShellGPT v2 Integration Test Suite")
    print("🧪 " * 20)
    
    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Tool Availability", test_tool_availability),
        ("Tool Command Generation", test_tool_command_generation),
        ("Safety Validation", test_safety_validator),
        ("Fact Extraction", test_fact_extraction),
        ("Agent Observation", test_agent_observe_phase),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)
