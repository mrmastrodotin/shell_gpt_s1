"""
Enum4linux Tool
SMB enumeration for Windows/Samba systems
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class Enum4linuxTool(BaseTool):
    """SMB enumeration using enum4linux"""
    
    spec = ToolSpec(
        name="enum4linux",
        binary="enum4linux",
        category=ToolCategory.ENUMERATION,
        phases=[RedTeamPhase.ENUMERATION],
        requires_root=False,
        destructive=False,
        description="SMB enumeration for Windows/Samba systems"
    )
    
    intents = [
        "enum_users",      # Enumerate users
        "enum_shares",     # Enumerate shares
        "enum_groups",     # Enumerate groups
        "enum_all"         # Full enumeration
    ]
    
    def generate_command(self, intent: str, context: Dict, facts: Dict) -> str:
        """Generate enum4linux command"""
        
        # Get target
        target = self._get_target(context, facts)
        if not target:
            return None
        
        if intent == "enum_users":
            # Enumerate users
            return f"enum4linux -U {target}"
        
        elif intent == "enum_shares":
            # Enumerate shares
            return f"enum4linux -S {target}"
        
        elif intent == "enum_groups":
            # Enumerate groups
            return f"enum4linux -G {target}"
        
        elif intent == "enum_all":
            # Full enumeration
            return f"enum4linux -a {target}"
        
        return None
    
    def _get_target(self, context: Dict, facts: Dict) -> str:
        """Extract target IP from context or facts"""
        
        # Check context
        if "target" in context:
            return context["target"]
        
        # Check facts for targets with SMB
        if "targets" in facts:
            for target in facts["targets"]:
                ports = target.get("ports", [])
                services = target.get("services", {})
                
                # Check for SMB ports
                if 139 in ports or 445 in ports:
                    return target["ip"]
                
                # Check for SMB in services
                for port, service in services.items():
                    if "smb" in service.lower() or "netbios" in service.lower():
                        return target["ip"]
        
        return None
    
    def parse_output(self, output: str) -> Dict:
        """Parse enum4linux output"""
        
        facts = {
            "users": [],
            "shares": [],
            "groups": [],
            "domain": None
        }
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract users
            if "S-1-5-21" in line and "(" in line:
                # Format: user:[username] rid:[0x...]
                if "user:[" in line:
                    start = line.find("user:[") + 6
                    end = line.find("]", start)
                    if start > 0 and end > 0:
                        username = line[start:end]
                        if username and username not in facts["users"]:
                            facts["users"].append(username)
            
            # Extract shares
            if "Sharename" in line or "\\\\\\\\".replace("\\", "") in line:
                parts = line.split()
                if len(parts) >= 2:
                    share = parts[0].strip()
                    if share and share not in ["Sharename", "IPC$", "ADMIN$"]:
                        if share not in facts["shares"]:
                            facts["shares"].append(share)
            
            # Extract domain
            if "Domain Name:" in line:
                facts["domain"] = line.split("Domain Name:")[-1].strip()
        
        return facts


# Register tool
def register():
    from sgpt.tools.registry import ToolRegistry
    return Enum4linuxTool()
