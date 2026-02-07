"""
Netcat Tool
Swiss army knife for networking
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class NetcatTool(BaseTool):
    """Netcat for network utilities and testing"""
    
    spec = ToolSpec(
        name="netcat",
        binary="nc",
        category=ToolCategory.EXPLOITATION,
        phases=[RedTeamPhase.RECONNAISSANCE, RedTeamPhase.ENUMERATION, RedTeamPhase.EXPLOITATION],
        requires_root=False,
        destructive=False,
        network_active=True,
        description="Networking utility",
        safe_flags=["-zv", "-v", "-w3"]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate netcat command"""
        
        target = None
        if facts.get('live_hosts'):
            target = facts['live_hosts'][0]
        elif context.get('target'):
            target = context['target']
            
        port = "80"
        
        if intent == "port_check":
            if not target: return None
            return f"nc -zv {target} {port}"
        
        elif intent == "banner_grab":
            if not target: return None
            return f"echo '' | nc -v -w3 {target} {port}"
        
        elif intent == "reverse_shell_listener":
            return f"nc -lvnp 4444"
        
        elif intent == "file_transfer":
            return f"nc -l -p 1234 > received_file.txt"
        
        return None
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse netcat output into structured facts"""
        
        facts = {}
        
        # Port check
        if 'succeeded' in output or 'open' in output.lower():
            facts['port_open'] = True
            
        # Banner grab (basic heuristic: if one line and short)
        if len(output.split('\n')) < 5 and len(output) > 5:
             facts['banner'] = output.strip()
             output_lower = output.lower()
             if 'ssh' in output_lower:
                 facts['service'] = 'SSH'
             elif 'http' in output_lower:
                 facts['service'] = 'HTTP'
             elif 'ftp' in output_lower:
                 facts['service'] = 'FTP'
             elif 'smtp' in output_lower:
                 facts['service'] = 'SMTP'
        
        return facts
