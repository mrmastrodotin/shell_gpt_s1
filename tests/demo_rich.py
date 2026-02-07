"""
Demo script for rich CLI formatting
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from sgpt.cli.formatter import AgentFormatter, header, phase, command, success, error, warning, info

print("\n" + "=" * 60)
print("Rich CLI Formatting Demo")
print("=" * 60 + "\n")

# Demo 1: Header
print("Demo 1: Header")
header("ShellGPT v2 - Red Team Automation", "Autonomous security testing agent")
time.sleep(1)

# Demo 2: Phase transition
print("\nDemo 2: Phase Transition")
phase("RECONNAISSANCE", "Discovering live hosts and services")
time.sleep(1)

# Demo 3: Command proposal
print("\nDemo 3: Command Proposal")
command("nmap -sn 192.168.1.0/24", tool="nmap")
time.sleep(1)

# Demo 4: Messages
print("\nDemo 4: Status Messages")
success("Command executed successfully")
warning("Rate limiting detected - waiting 5 seconds")
error("Connection timeout", details="Target host unreachable after 3 retries")
info("Session saved to disk")
time.sleep(1)

# Demo 5: Execution panel
print("\nDemo 5: Execution Instructions")
AgentFormatter.print_execution("exec_abc123", "nmap -sn 192.168.1.0/24")
time.sleep(1)

# Demo 6: Result
print("\nDemo 6: Execution Result")
AgentFormatter.print_result(
    exit_code=0,
    output="Starting Nmap 7.94\\nHost is up (0.00012s latency)\\nNmap done: 256 IP addresses scanned in 2.45 seconds"
)
time.sleep(1)

# Demo 7: Facts table
print("\nDemo 7: Discovered Facts")
facts = {
    'live_hosts': ['192.168.1.1', '192.168.1.10', '192.168.1.20', '192.168.1.50'],
    'open_ports': [
        {'ip': '192.168.1.1', 'port': 80},
        {'ip': '192.168.1.1', 'port': 443},
        {'ip': '192.168.1.10', 'port': 22}
    ],
    'vulnerabilities': [
        {'severity': 'critical', 'name': 'SQL Injection'},
        {'severity': 'high', 'name': 'XSS'}
    ],
    'targets': ['192.168.1.1', '192.168.1.10']
}
AgentFormatter.print_facts(facts)
time.sleep(1)

# Demo 8: Tools table
print("\nDemo 8: Tool Availability")
tools = {
    'nmap': True,
    'curl': True,
    'gobuster': True,
    'nikto': False,
    'enum4linux': True,
    'hydra': False,
    'whatweb': True,
    'python_script': True
}
AgentFormatter.print_tools(tools)
time.sleep(1)

# Demo 9: Session summary
print("\nDemo 9: Session Summary")
session = {
    'session_id': 'agent_abc123',
    'goal': 'Enumerate 192.168.1.0/24',
    'phase': 'enumeration',
    'commands_executed': ['cmd1', 'cmd2', 'cmd3'],
    'facts': facts,
    'done': False
}
AgentFormatter.print_session_summary(session)
time.sleep(1)

# Demo 10: Progress bar
print("\nDemo 10: Progress Bar")
progress = AgentFormatter.create_progress()
with progress:
    task = progress.add_task("[cyan]Scanning network...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
        time.sleep(0.02)

print("\n" + "=" * 60)
print("✅ Demo Complete!")
print("=" * 60)
