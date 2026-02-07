"""
Python Script Tool
Generates and executes custom Python scripts for red-team tasks
"""

import json
from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase


class PythonScriptTool(BaseTool):
    """Python script generator and executor"""
    
    spec = ToolSpec(
        name="python_script",
        binary="python",
        category=ToolCategory.SCRIPTING,
        phases=[
            RedTeamPhase.RECON,
            RedTeamPhase.ENUMERATION,
            RedTeamPhase.VULNERABILITY_SCAN,
            RedTeamPhase.EXPLOITATION,
            RedTeamPhase.POST_EXPLOITATION
        ],
        requires_root=False,
        destructive=False,  # Scripts themselves can be reviewed via HIL
        network_active=True,
        description="Generate custom Python scripts for specialized tasks",
        safe_flags=["-c", "-m"]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate Python script command based on intent"""
        
        if intent == "port_banner_grab":
            # Custom banner grabbing script
            hosts = facts.get("live_hosts", [])
            if not hosts:
                return None
            
            target = hosts[0]
            script = f'''
import socket
target = "{target}"
ports = [21, 22, 23, 25, 80, 443, 3306, 5432, 8080]
for port in ports:
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((target, port))
        banner = s.recv(1024).decode().strip()
        if banner:
            print(f"Port {{port}}: {{banner[:100]}}")
        s.close()
    except:
        pass
'''
            return f'python -c "{script}"'
        
        elif intent == "http_scanner":
            # HTTP service scanner
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            target_list = [t["ip"] for t in targets]
            script = f'''
import requests
targets = {json.dumps(target_list)}
for ip in targets:
    for port in [80, 443, 8080, 8443]:
        for proto in ["http", "https"]:
            try:
                r = requests.get(f"{{proto}}://{{ip}}:{{port}}", timeout=3, verify=False)
                print(f"{{proto}}://{{ip}}:{{port}} - {{r.status_code}} {{r.headers.get('Server', '')}}")
            except:
                pass
'''
            return f'python -c "{script}"'
        
        elif intent == "subnet_scanner":
            # Quick subnet scanner
            subnet = context.get("network", {}).get("subnet", "192.168.0.0/24")
            subnet_base = ".".join(subnet.split(".")[:3])
            
            script = f'''
import subprocess
import concurrent.futures
def ping(ip):
    result = subprocess.run(["ping", "-n", "1", "-w", "500", ip], 
                          capture_output=True, text=True)
    if "TTL=" in result.stdout:
        print(f"{{ip}} - UP")
for i in range(1, 255):
    ping(f"{subnet_base}.{{i}}")
'''
            return f'python -c "{script}"'
        
        elif intent == "data_exfil_prep":
            # Prepare data for exfiltration (base64 encode)
            script = '''
import base64
import sys
data = sys.stdin.read()
encoded = base64.b64encode(data.encode()).decode()
print(encoded)
'''
            return f'python -c "{script}"'
        
        return None
    
    def parse_output(self, output: str) -> dict:
        """Parse Python script output"""
        facts = {
            "hosts": [],
            "targets": [],
            "services": {}
        }
        
        # Parse "IP - UP" format from subnet scanner
        for line in output.split("\n"):
            if " - UP" in line:
                ip = line.split(" - ")[0].strip()
                facts["hosts"].append(ip)
            
            # Parse "Port X: banner" format
            if "Port " in line and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    port_part = parts[0].replace("Port", "").strip()
                    banner = parts[1].strip()
                    # Would need IP context to properly store
                    facts["services"][port_part] = banner
        
        return facts
