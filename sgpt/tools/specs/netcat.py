"""
Netcat Tool
Swiss army knife for networking
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class NetcatTool(BaseTool):
    """Netcat for network utilities and testing"""
    
    def __init__(self):
        super().__init__(
            name="netcat",
            category=ToolCategory.EXPLOITATION,
            intents=[
                "port_check",
                "banner_grab",
                "reverse_shell_listener",
                "file_transfer"
            ]
        )
    
    def get_spec(self, intent: str) -> ToolSpec:
        """Get tool specification for given intent"""
        
        specs = {
            "port_check": ToolSpec(
                description="Check if port is open on target",
                parameters={
                    "target": "Target IP or hostname",
                    "port": "Port number"
                },
                example="nc -zv 192.168.1.10 80",
                phase=RedTeamPhase.RECONNAISSANCE,
                risk_level="low"
            ),
            
            "banner_grab": ToolSpec(
                description="Grab service banner from port",
                parameters={
                    "target": "Target IP or hostname",
                    "port": "Port number"
                },
                example="nc -v 192.168.1.10 80",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "reverse_shell_listener": ToolSpec(
                description="Listen for reverse shell connection",
                parameters={
                    "port": "Local port to listen on"
                },
                example="nc -lvnp 4444",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="high"
            ),
            
            "file_transfer": ToolSpec(
                description="Transfer file to/from target",
                parameters={
                    "mode": "Mode: 'send' or 'receive'",
                    "target": "Target IP (for send mode)",
                    "port": "Port number",
                    "file": "File path"
                },
                example="nc -l -p 1234 > received_file.txt",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="medium"
            )
        }
        
        return specs.get(intent)
    
    def build_command(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Build netcat command"""
        
        if intent == "port_check":
            target = parameters.get('target')
            port = parameters.get('port')
            return f"nc -zv {target} {port}"
        
        elif intent == "banner_grab":
            target = parameters.get('target')
            port = parameters.get('port')
            return f"echo '' | nc -v -w3 {target} {port}"
        
        elif intent == "reverse_shell_listener":
            port = parameters.get('port')
            return f"nc -lvnp {port}"
        
        elif intent == "file_transfer":
            mode = parameters.get('mode')
            port = parameters.get('port')
            file = parameters.get('file')
            
            if mode == 'receive':
                return f"nc -l -p {port} > {file}"
            elif mode == 'send':
                target = parameters.get('target')
                return f"nc {target} {port} < {file}"
        
        return None
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for intent"""
        
        if intent in ["port_check", "banner_grab"]:
            return 'target' in parameters and 'port' in parameters
        
        if intent == "reverse_shell_listener":
            return 'port' in parameters
        
        if intent == "file_transfer":
            return 'mode' in parameters and 'port' in parameters and 'file' in parameters
        
        return True
    
    def parse_output(self, intent: str, output: str) -> Dict[str, Any]:
        """Parse netcat output into structured facts"""
        
        facts = {}
        
        if intent == "port_check":
            facts['port_open'] = 'succeeded' in output or 'open' in output.lower()
        
        elif intent == "banner_grab":
            # The output itself is the banner
            facts['banner'] = output.strip()
            
            # Try to identify service
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
