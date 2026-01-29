"""
Masscan Tool
Ultra-fast port scanner
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class MasscanTool(BaseTool):
    """Masscan for ultra-fast port scanning"""
    
    def __init__(self):
        super().__init__(
            name="masscan",
            category=ToolCategory.DISCOVERY,
            intents=[
                "fast_port_scan",
                "full_port_scan",
                "specific_ports"
            ]
        )
    
    def get_spec(self, intent: str) -> ToolSpec:
        """Get tool specification for given intent"""
        
        specs = {
            "fast_port_scan": ToolSpec(
                description="Fast scan of common ports on subnet",
                parameters={
                    "target": "Target IP range or subnet",
                    "ports": "Port range (optional, default: top 100)",
                    "rate": "Packets per second (optional, default: 1000)"
                },
                example="masscan 192.168.1.0/24 -p80,443 --rate=1000",
                phase=RedTeamPhase.RECONNAISSANCE,
                risk_level="low"
            ),
            
            "full_port_scan": ToolSpec(
                description="Scan all 65535 ports (very fast but noisy)",
                parameters={
                    "target": "Target IP or subnet",
                    "rate": "Packets per second (default: 1000)"
                },
                example="masscan 192.168.1.10 -p1-65535 --rate=10000",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="medium"
            ),
            
            "specific_ports": ToolSpec(
                description="Scan specific port list on targets",
                parameters={
                    "target": "Target IP range",
                    "ports": "Comma-separated port list",
                    "rate": "Packets per second (optional)"
                },
                example="masscan 10.0.0.0/8 -p21,22,80,443,3389",
                phase=RedTeamPhase.RECONNAISSANCE,
                risk_level="low"
            )
        }
        
        return specs.get(intent)
    
    def build_command(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Build masscan command"""
        
        target = parameters.get('target')
        
        if intent == "fast_port_scan":
            ports = parameters.get('ports', '80,443,8080,22,21,3389')
            rate = parameters.get('rate', '1000')
            return f"masscan {target} -p{ports} --rate={rate}"
        
        elif intent == "full_port_scan":
            rate = parameters.get('rate', '1000')
            return f"masscan {target} -p1-65535 --rate={rate}"
        
        elif intent == "specific_ports":
            ports = parameters.get('ports')
            rate = parameters.get('rate', '1000')
            cmd = f"masscan {target} -p{ports}"
            if rate:
                cmd += f" --rate={rate}"
            return cmd
        
        return None
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for intent"""
        
        if not parameters.get('target'):
            return False
        
        if intent == "specific_ports":
            return 'ports' in parameters
        
        return True
    
    def parse_output(self, intent: str, output: str) -> Dict[str, Any]:
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
