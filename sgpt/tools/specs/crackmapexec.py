"""
CrackMapExec Tool
Network penetration testing and lateral movement
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class CrackMapExecTool(BaseTool):
    """CrackMapExec for SMB/WinRM exploitation"""
    
    def __init__(self):
        super().__init__(
            name="crackmapexec",
            category=ToolCategory.EXPLOITATION,
            intents=[
                "smb_enumeration",
                "smb_login",
                "smb_shares",
                "execute_command"
            ]
        )
    
    def get_spec(self, intent: str) -> ToolSpec:
        """Get tool specification for given intent"""
        
        specs = {
            "smb_enumeration": ToolSpec(
                description="Enumerate SMB hosts and gather information",
                parameters={
                    "target": "Target IP or subnet"
                },
                example="crackmapexec smb 192.168.1.0/24",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "smb_login": ToolSpec(
                description="Test credentials against SMB",
                parameters={
                    "target": "Target IP or subnet",
                    "username": "Username",
                    "password": "Password or password file",
                    "domain": "Domain (optional)"
                },
                example="crackmapexec smb 192.168.1.10 -u admin -p password123",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="medium"
            ),
            
            "smb_shares": ToolSpec(
                description="Enumerate shares with credentials",
                parameters={
                    "target": "Target IP",
                    "username": "Username",
                    "password": "Password",
                    "domain": "Domain (optional)"
                },
                example="crackmapexec smb 192.168.1.10 -u admin -p pass --shares",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "execute_command": ToolSpec(
                description="Execute command on remote system via SMB",
                parameters={
                    "target": "Target IP",
                    "username": "Username",
                    "password": "Password",
                    "command": "Command to execute",
                    "domain": "Domain (optional)"
                },
                example="crackmapexec smb 192.168.1.10 -u admin -p pass -x 'whoami'",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="high"
            )
        }
        
        return specs.get(intent)
    
    def build_command(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Build crackmapexec command"""
        
        target = parameters.get('target')
        
        if intent == "smb_enumeration":
            return f"crackmapexec smb {target}"
        
        elif intent == "smb_login":
            username = parameters.get('username')
            password = parameters.get('password')
            domain = parameters.get('domain')
            
            cmd = f"crackmapexec smb {target} -u {username} -p {password}"
            
            if domain:
                cmd += f" -d {domain}"
            
            return cmd
        
        elif intent == "smb_shares":
            username = parameters.get('username')
            password = parameters.get('password')
            domain = parameters.get('domain')
            
            cmd = f"crackmapexec smb {target} -u {username} -p {password} --shares"
            
            if domain:
                cmd += f" -d {domain}"
            
            return cmd
        
        elif intent == "execute_command":
            username = parameters.get('username')
            password = parameters.get('password')
            command = parameters.get('command')
            domain = parameters.get('domain')
            
            cmd = f"crackmapexec smb {target} -u {username} -p {password} -x '{command}'"
            
            if domain:
                cmd += f" -d {domain}"
            
            return cmd
        
        return None
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for intent"""
        
        if not parameters.get('target'):
            return False
        
        if intent in ["smb_login", "smb_shares", "execute_command"]:
            return 'username' in parameters and 'password' in parameters
        
        if intent == "execute_command" and not parameters.get('command'):
            return False
        
        return True
    
    def parse_output(self, intent: str, output: str) -> Dict[str, Any]:
        """Parse crackmapexec output into structured facts"""
        
        facts = {}
        
        if intent == "smb_enumeration":
            # Extract discovered hosts
            facts['hosts'] = []
            
            for line in output.split('\n'):
                if 'SMB' in line and '445' in line:
                    parts = line.split()
                    if len(parts) > 2:
                        ip = parts[1]
                        facts['hosts'].append({
                            'ip': ip,
                            'os': ' '.join(parts[4:]) if len(parts) > 4 else 'Unknown'
                        })
        
        elif intent == "smb_login":
            # Check for successful authentication
            facts['authenticated'] = '[+]' in output or 'Pwn3d!' in output
            facts['admin_access'] = 'Pwn3d!' in output
        
        elif intent == "smb_shares":
            # Extract share names
            facts['shares'] = []
            
            for line in output.split('\n'):
                if 'READ' in line or 'WRITE' in line:
                    # Parse share info
                    parts = line.split()
                    if len(parts) > 0:
                        share_info = {
                            'name': parts[0] if parts else 'Unknown',
                            'permissions': 'READ' if 'READ' in line else 'WRITE'
                        }
                        facts['shares'].append(share_info)
        
        elif intent == "execute_command":
            # Extract command output
            facts['command_output'] = output
            facts['success'] = 'error' not in output.lower()
        
        return facts
