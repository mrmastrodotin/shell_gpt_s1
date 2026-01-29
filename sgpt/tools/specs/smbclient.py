"""
SMBClient Tool
Interact with SMB shares and perform file operations
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class SMBClientTool(BaseTool):
    """SMBClient for SMB interaction and file operations"""
    
    def __init__(self):
        super().__init__(
            name="smbclient",
            category=ToolCategory.ENUMERATION,
            intents=[
                "list_shares",
                "list_files",
                "download_file",
                "check_access"
            ]
        )
    
    def get_spec(self, intent: str) -> ToolSpec:
        """Get tool specification for given intent"""
        
        specs = {
            "list_shares": ToolSpec(
                description="List available SMB shares on target",
                parameters={
                    "target": "Target IP or hostname",
                    "username": "Username (optional, default: guest)",
                    "password": "Password (optional, default: empty)"
                },
                example="smbclient -L //192.168.1.10 -N",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "list_files": ToolSpec(
                description="List files in SMB share",
                parameters={
                    "target": "Target IP or hostname",
                    "share": "Share name",
                    "directory": "Directory path (optional, default: /)",
                    "username": "Username (optional)",
                    "password": "Password (optional)"
                },
                example="smbclient //192.168.1.10/share -c 'ls'",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "download_file": ToolSpec(
                description="Download file from SMB share",
                parameters={
                    "target": "Target IP or hostname",
                    "share": "Share name",
                    "remote_file": "Remote file path",
                    "local_file": "Local save path",
                    "username": "Username (optional)",
                    "password": "Password (optional)"
                },
                example="smbclient //192.168.1.10/share -c 'get file.txt'",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="medium"
            ),
            
            "check_access": ToolSpec(
                description="Check anonymous or guest access to shares",
                parameters={
                    "target": "Target IP or hostname",
                    "share": "Share name (optional)",
                    "username": "Username to test (optional)"
                },
                example="smbclient //192.168.1.10/IPC$ -N",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            )
        }
        
        return specs.get(intent)
    
    def build_command(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Build smbclient command"""
        
        target = parameters.get('target')
        
        if intent == "list_shares":
            # List shares on target
            cmd = f"smbclient -L //{target}"
            
            username = parameters.get('username')
            password = parameters.get('password')
            
            if username:
                cmd += f" -U {username}"
                if password:
                    cmd += f"%{password}"
            else:
                cmd += " -N"  # No password (anonymous)
            
            return cmd
        
        elif intent == "list_files":
            # List files in share
            share = parameters.get('share')
            directory = parameters.get('directory', '/')
            
            cmd = f"smbclient //{target}/{share}"
            
            username = parameters.get('username')
            password = parameters.get('password')
            
            if username:
                cmd += f" -U {username}"
                if password:
                    cmd += f"%{password}"
            else:
                cmd += " -N"
            
            # Add list command
            cmd += f" -c 'cd {directory}; ls'"
            
            return cmd
        
        elif intent == "download_file":
            # Download file from share
            share = parameters.get('share')
            remote_file = parameters.get('remote_file')
            local_file = parameters.get('local_file', remote_file)
            
            cmd = f"smbclient //{target}/{share}"
            
            username = parameters.get('username')
            password = parameters.get('password')
            
            if username:
                cmd += f" -U {username}"
                if password:
                    cmd += f"%{password}"
            else:
                cmd += " -N"
            
            # Add get command
            cmd += f" -c 'get {remote_file} {local_file}'"
            
            return cmd
        
        elif intent == "check_access":
            # Check access to share
            share = parameters.get('share', 'IPC$')
            
            cmd = f"smbclient //{target}/{share}"
            
            username = parameters.get('username')
            
            if username:
                cmd += f" -U {username}"
            else:
                cmd += " -N"
            
            # Just try to connect
            cmd += " -c 'ls'"
            
            return cmd
        
        return None
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for intent"""
        
        spec = self.get_spec(intent)
        if not spec:
            return False
        
        required_params = spec.parameters
        
        # Check required parameters
        if intent in ["list_shares", "check_access"]:
            return 'target' in parameters
        
        elif intent == "list_files":
            return 'target' in parameters and 'share' in parameters
        
        elif intent == "download_file":
            return all(k in parameters for k in ['target', 'share', 'remote_file'])
        
        return False
    
    def parse_output(self, intent: str, output: str) -> Dict[str, Any]:
        """Parse smbclient output into structured facts"""
        
        facts = {}
        
        if intent == "list_shares":
            # Parse share listing
            shares = []
            lines = output.split('\n')
            
            for line in lines:
                if 'Disk' in line or 'IPC' in line or 'Printer' in line:
                    parts = line.split()
                    if parts:
                        share_name = parts[0]
                        share_type = 'Disk' if 'Disk' in line else ('IPC' if 'IPC' in line else 'Printer')
                        shares.append({
                            'name': share_name,
                            'type': share_type,
                            'comment': ' '.join(parts[2:]) if len(parts) > 2 else ''
                        })
            
            facts['shares'] = shares
        
        elif intent == "list_files":
            # Parse file listing
            files = []
            lines = output.split('\n')
            
            for line in lines:
                # Look for file entries (they typically have size and date)
                if line.strip() and not line.startswith('.') and 'blocks' not in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        files.append({
                            'name': parts[0],
                            'size': parts[1] if parts[1].isdigit() else None,
                            'attributes': parts[2] if len(parts) > 2 else None
                        })
            
            facts['files'] = files
        
        elif intent == "check_access":
            # Check if access was successful
            facts['access_granted'] = 'NT_STATUS_ACCESS_DENIED' not in output and 'NT_STATUS_LOGON_FAILURE' not in output
            facts['anonymous_access'] = 'NT_STATUS_ACCESS_DENIED' not in output
        
        return facts
