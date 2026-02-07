"""
Hydra Tool
Password brute-forcing for multiple protocols
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class HydraTool(BaseTool):
    """Password brute-forcing using hydra"""
    
    spec = ToolSpec(
        name="hydra",
        binary="hydra",
        category=ToolCategory.EXPLOITATION,
        phases=[RedTeamPhase.EXPLOITATION],
        requires_root=False,
        destructive=False,  # Brute-forcing is aggressive but not destructive
        description="Fast password brute-forcing for multiple protocols"
    )
    
    intents = [
        "ssh_brute",      # SSH brute-force
        "ftp_brute",      # FTP brute-force
        "http_brute",     # HTTP basic auth brute-force
        "rdp_brute"       # RDP brute-force
    ]
    
    def generate_command(self, intent: str, context: Dict, facts: Dict) -> str:
        """Generate hydra command"""
        
        # Get target
        target = self._get_target_for_service(intent, context, facts)
        if not target:
            return None
        
        # Check for credentials wordlist
        wordlist = context.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        username = context.get("username", "admin")
        
        if intent == "ssh_brute":
            # SSH brute-force
            return f"hydra -l {username} -P {wordlist} ssh://{target} -t 4"
        
        elif intent == "ftp_brute":
            # FTP brute-force
            return f"hydra -l {username} -P {wordlist} ftp://{target} -t 4"
        
        elif intent == "http_brute":
            # HTTP basic auth
            # Format: hydra -l user -P pass.txt target http-get /path
            path = context.get("path", "/")
            return f"hydra -l {username} -P {wordlist} {target} http-get {path} -t 4"
        
        elif intent == "rdp_brute":
            # RDP brute-force
            return f"hydra -l {username} -P {wordlist} rdp://{target} -t 1"
        
        return None
    
    def _get_target_for_service(self, intent: str, context: Dict, facts: Dict) -> str:
        """Get target IP based on service"""
        
        # Check context first
        if "target" in context:
            return context["target"]
        
        # Map intents to ports
        service_ports = {
            "ssh_brute": [22],
            "ftp_brute": [21],
            "http_brute": [80, 8080, 443],
            "rdp_brute": [3389]
        }
        
        required_ports = service_ports.get(intent, [])
        
        # Check facts for targets with required port
        if "targets" in facts:
            for target in facts["targets"]:
                ports = target.get("ports", [])
                
                for required_port in required_ports:
                    if required_port in ports:
                        return target["ip"]
        
        return None
    
    def parse_output(self, output: str) -> Dict:
        """Parse hydra output"""
        
        facts = {
            "credentials": [],
            "attempts": 0,
            "success": False
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract successful credentials
            if "[22][ssh]" in line or "[21][ftp]" in line or "login:" in line:
                if "host:" in line and "login:" in line and "password:" in line:
                    # Parse: [port][service] host: IP login: USER password: PASS
                    parts = line.split()
                    credential = {}
                    
                    for i, part in enumerate(parts):
                        if part == "host:":
                            credential["host"] = parts[i + 1]
                        elif part == "login:":
                            credential["username"] = parts[i + 1]
                        elif part == "password:":
                            credential["password"] = parts[i + 1]
                    
                    if credential:
                        facts["credentials"].append(credential)
                        facts["success"] = True
            
            # Count attempts
            if "attempt" in line.lower():
                try:
                    # Extract number
                    parts = line.split()
                    for part in parts:
                        if part.isdigit():
                            facts["attempts"] = int(part)
                            break
                except:
                    pass
        
        return facts


# Register tool
def register():
    from sgpt.tools.registry import ToolRegistry
    return HydraTool()
