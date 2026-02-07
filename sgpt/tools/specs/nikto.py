"""
Nikto Tool Implementation
Web server vulnerability scanner
"""

import re
from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase, Vulnerability


class NiktoTool(BaseTool):
    """Nikto web vulnerability scanner"""
    
    spec = ToolSpec(
        name="nikto",
        binary="nikto",
        category=ToolCategory.WEB,
        phases=[RedTeamPhase.VULNERABILITY_SCAN],
        requires_root=False,
        destructive=False,
        network_active=True,
        description="Web server vulnerability scanner",
        safe_flags=[
            "-h",           # Host
            "-p",           # Port
            "-ssl",         # Force SSL
            "-nossl",       # Force no SSL
            "-Tuning",      # Scan tuning
            "-Display",     # Display options
            "-o",           # Output
            "-Format",      # Output format
        ]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate nikto command based on intent"""
        
        if intent == "web_vuln_scan":
            # Vulnerability scan on web service
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        ssl_flag = "-ssl" if ("ssl" in service.lower() or port == 443) else "-nossl"
                        return f"nikto -h {ip} -p {port} {ssl_flag} -Tuning x 6"
            
            return None
        
        elif intent == "quick_web_scan":
            # Quick scan
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        return f"nikto -h {ip}:{port} -Tuning 1 2 3"
            
            return None
        
        return None
    
    def parse_output(self, output: str) -> dict:
        """Parse nikto output to extract vulnerabilities"""
        facts = {
            "vulnerabilities": [],
            "web_info": []
        }
        
        # Parse findings
        # Format: + OSVDB-XXXX: /path: Description
        for line in output.split("\n"):
            if line.startswith("+ "):
                # Extract vulnerability info
                vuln_match = re.search(r'\+ (?:OSVDB-(\d+)|CVE-[\d-]+):\s*(.+)', line)
                if vuln_match:
                    vuln_id = vuln_match.group(1) if vuln_match.group(1) else "Unknown"
                    description = vuln_match.group(2).strip()
                    
                    facts["vulnerabilities"].append({
                        "cve_id": f"OSVDB-{vuln_id}",
                        "name": "Nikto Finding",
                        "severity": "medium",  # Default
                        "description": description,
                        "port": 80,  # Would need to extract from context
                        "target": ""  # Would need IP context
                    })
            
            # Extract server info
            if "Server:" in line:
                server_match = re.search(r'Server:\s*(.+)', line)
                if server_match:
                    facts["web_info"].append({"server": server_match.group(1).strip()})
        
        return facts
