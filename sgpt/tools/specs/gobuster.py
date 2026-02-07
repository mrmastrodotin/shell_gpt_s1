"""
Gobuster Tool Implementation
Directory and DNS brute-forcing tool
"""

import re
from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase


class GobusterTool(BaseTool):
    """Gobuster directory/DNS brute-forcer"""
    
    spec = ToolSpec(
        name="gobuster",
        binary="gobuster",
        category=ToolCategory.WEB,
        phases=[RedTeamPhase.ENUMERATION, RedTeamPhase.VULNERABILITY_SCAN],
        requires_root=False,
        destructive=False,
        network_active=True,
        description="Directory and DNS brute-forcing",
        safe_flags=[
            "dir",          # Directory mode
            "dns",          # DNS mode
            "vhost",        # Virtual host mode
            "-u",           # URL
            "-w",           # Wordlist
            "-t",           # Threads
            "-q",           # Quiet
            "-k",           # Skip SSL verification
            "-x",           # Extensions
            "--wildcard",   # Wildcard detection
        ]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate gobuster command based on intent"""
        
        if intent == "dir_enum":
            # Directory enumeration
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            # Find target with HTTP service
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        protocol = "https" if port == 443 else "http"
                        # Use common wordlist
                        wordlist = "/usr/share/wordlists/dirb/common.txt"
                        return f"gobuster dir -u {protocol}://{ip}:{port} -w {wordlist} -q -k"
            
            return None
        
        elif intent == "dir_enum_extensions":
            # Directory enumeration with file extensions
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        protocol = "https" if port == 443 else "http"
                        wordlist = "/usr/share/wordlists/dirb/common.txt"
                        return f"gobuster dir -u {protocol}://{ip}:{port} -w {wordlist} -x php,html,txt -q -k"
            
            return None
        
        elif intent == "vhost_enum":
            # Virtual host enumeration
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                hostname = target.get("hostname", target["ip"])
                for port, service in services.items():
                    if "http" in service.lower():
                        protocol = "https" if port == 443 else "http"
                        wordlist = "/usr/share/wordlists/dirb/common.txt"
                        return f"gobuster vhost -u {protocol}://{hostname}:{port} -w {wordlist} -q -k"
            
            return None
        
        return None
    
    def parse_output(self, output: str) -> dict:
        """Parse gobuster output to extract facts"""
        facts = {
            "directories": [],
            "files": [],
            "vhosts": []
        }
        
        # Parse directory/file findings
        # Format: /path (Status: 200) [Size: 1234]
        for line in output.split("\n"):
            if "(Status:" in line:
                path_match = re.search(r'^(/[^\s]+)', line)
                status_match = re.search(r'Status:\s*(\d+)', line)
                
                if path_match and status_match:
                    path = path_match.group(1)
                    status = status_match.group(1)
                    
                    if path.endswith('/'):
                        facts["directories"].append({"path": path, "status": status})
                    else:
                        facts["files"].append({"path": path, "status": status})
            
            # Parse vhost findings
            if "Found:" in line:
                vhost_match = re.search(r'Found:\s*(\S+)', line)
                if vhost_match:
                    facts["vhosts"].append(vhost_match.group(1))
        
        return facts
