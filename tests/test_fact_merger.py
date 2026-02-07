"""
Test Fact Merger
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.agent.state import AgentState, Target
from sgpt.agent.fact_merger import FactMerger

print("=" * 60)
print("Testing Fact Merger")
print("=" * 60)

# Initialize state
state = AgentState.initialize(
    session_id="test_merger",
    goal="Test fact merging"
)

# Test 1: Merge hosts
print("\n✓ Test 1: Merge Hosts")
new_facts = {"hosts": ["192.168.1.1", "192.168.1.10", "192.168.1.20"]}
FactMerger.merge_into_state(state, new_facts)
assert len(state.facts.live_hosts) == 3
print(f"  ✅ Merged {len(state.facts.live_hosts)} hosts")

# Test 2: Deduplicate hosts
print("\n✓ Test 2: Deduplicate Hosts")
new_facts = {"hosts": ["192.168.1.1", "192.168.1.30"]}  # 1.1 is duplicate
FactMerger.merge_into_state(state, new_facts)
assert len(state.facts.live_hosts) == 4  # Should be 3 + 1 new
print(f"  ✅ Deduplicated: {len(state.facts.live_hosts)} unique hosts")

# Test 3: Merge targets
print("\n✓ Test 3: Merge Targets")
new_facts = {
    "targets": [
        {
            "ip": "192.168.1.1",
            "ports": [22, 80],
            "services": {22: "SSH", 80: "Apache"}
        }
    ]
}
FactMerger.merge_into_state(state, new_facts)
assert len(state.facts.targets) == 1
assert len(state.facts.targets[0].ports) == 2
print(f"  ✅ Created target: {state.facts.targets[0].ip}")
print(f"     Ports: {state.facts.targets[0].ports}")

# Test 4: Update existing target
print("\n✓ Test 4: Update Existing Target")
new_facts = {
    "targets": [
        {
            "ip": "192.168.1.1",  # Same IP
            "ports": [443],  # New port
            "services": {443: "HTTPS"}
        }
    ]
}
FactMerger.merge_into_state(state, new_facts)
assert len(state.facts.targets) == 1  # Still 1 target
assert 22 in state.facts.targets[0].ports
assert 80 in state.facts.targets[0].ports
assert 443 in state.facts.targets[0].ports
print(f"  ✅ Updated target ports: {state.facts.targets[0].ports}")

# Test 5: Merge vulnerabilities
print("\n✓ Test 5: Merge Vulnerabilities")
new_facts = {
    "vulnerabilities": [
        {
            "cve_id": "CVE-2021-1234",
            "name": "Test Vuln",
            "severity": "high",
            "target": "192.168.1.1",
            "port": 80,
            "description": "Test",
            "exploit_available": True
        }
    ]
}
FactMerger.merge_into_state(state, new_facts)
assert len(state.facts.vulnerabilities) == 1
print(f"  ✅ Merged vulnerability: {state.facts.vulnerabilities[0].cve_id}")

# Test 6: Deduplicate vulnerabilities
print("\n✓ Test 6: Deduplicate Vulnerabilities")
FactMerger.merge_into_state(state, new_facts)  # Same vuln
assert len(state.facts.vulnerabilities) == 1  # Should still be 1
print(f"  ✅ Deduplicated vulnerabilities: {len(state.facts.vulnerabilities)}")

# Test 7: Get summary
print("\n✓ Test 7: Get Summary")
summary = FactMerger.get_summary(state.facts)
print(f"  ✅ Summary:")
print(f"     Hosts: {summary['hosts_discovered']}")
print(f"     Targets: {summary['targets_identified']}")
print(f"     Ports: {summary['total_ports']}")
print(f"     Vulnerabilities: {summary['vulnerabilities_found']}")

print("\n" + "=" * 60)
print("All Tests Passed! ✅")
print("=" * 60)
print("\nFact merging system is operational!")
