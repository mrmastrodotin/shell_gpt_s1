"""
Masscan Tool
Ultra-fast port scanner
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class MasscanTool(BaseTool):
    """Masscan for ultra-fast port scanning"""
    
    spec = ToolSpec(
        name="masscan",
        binary="masscan",
        category=ToolCategory.DISCOVERY,
        phases=[RedTeamPhase.RECON, RedTeamPhase.RECONNAISSANCE],
        requires_root=True,
        destructive=False,
        network_active=True,
        description="Ultra-fast port scanner",
        safe_flags=["-p", "--rate"]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate masscan command based on intent"""
        
        # Extract parameters from context/facts
        target = None
        if context.get('network', {}).get('subnet'):
            target = context['network']['subnet']
        elif facts.get('live_hosts'):
            target = facts['live_hosts'][0]
            
        if not target:
            return None
            
        if intent == "fast_port_scan":
            ports = "80,443,8080,22,21,3389"
            rate = "1000"
            return f"masscan {target} -p{ports} --rate={rate}"
        
        elif intent == "full_port_scan":
            rate = "1000"
            return f"masscan {target} -p1-65535 --rate={rate}"
        
        elif intent == "specific_ports":
            # Just example ports if not specified in intent context
            ports = "80,443"
            return f"masscan {target} -p{ports}"
        
        return None
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse masscan output into structured facts"""
        
        facts = {'open_ports': []}
        
        # Masscan output format: Discovered open port 80/tcp on 192.168.1.1
        lines = output.split('\n')
        
        for line in lines:
            if 'Discovered open port' in line:
                parts = line.split()
                if len(parts) >= 6:
                    port_proto = parts[3]  # e.g., "80/tcp"
                    ip = parts[5]
                    
                    port = port_proto.split('/')[0]
                    facts['open_ports'].append({
                        'ip': ip,
                        'port': int(port),
                        'protocol': 'tcp'
                    })
        
        return facts
