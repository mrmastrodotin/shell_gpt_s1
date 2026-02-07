"""
SMBClient Tool
Interact with SMB shares and perform file operations
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class SMBClientTool(BaseTool):
    """SMBClient for SMB interaction and file operations"""
    
    spec = ToolSpec(
        name="smbclient",
        binary="smbclient",
        category=ToolCategory.ENUMERATION,
        phases=[RedTeamPhase.ENUMERATION, RedTeamPhase.EXPLOITATION],
        requires_root=False,
        destructive=False,
        network_active=True,
        description="SMB interaction tool",
        safe_flags=["-L", "-N", "-U", "-c"]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate smbclient command"""
        
        # Extract target from facts
        target = None
        if facts.get('live_hosts'):
            target = facts['live_hosts'][0]
        elif facts.get('targets'):
            target = facts['targets'][0]['ip']
            
        if not target:
            return None
            
        # Default credentials
        username = "guest"
        password = None
        
        # Check facts for credentials
        if facts.get('credentials'):
            # Simple logic: pick first credential for target
            for cred in facts['credentials']:
                if cred.get('target') == target or cred.get('ip') == target:
                    username = cred.get('username', username)
                    password = cred.get('password', password)
                    break
        
        if intent == "list_shares":
            cmd = f"smbclient -L //{target}"
            if username != "guest" or password:
                cmd += f" -U {username}"
                if password:
                    cmd += f"%{password}"
            else:
                cmd += " -N"
            return cmd
        
        elif intent == "list_files":
            share = context.get('share', 'IPC$')
            directory = context.get('directory')
            
            cmd_str = "ls"
            if directory:
                cmd_str = f"cd {directory}; ls"
                
            cmd = f"smbclient //{target}/{share} -U {username} -c '{cmd_str}'"
            return cmd
        
        elif intent == "download_file":
            share = context.get('share', 'Users')
            remote_file = context.get('remote_file', 'flag.txt')
            local_file = context.get('local_file', 'flag.txt')
            cmd = f"smbclient //{target}/{share} -U {username} -c 'get {remote_file} {local_file}'"
            return cmd
        
        elif intent == "check_access":
            share = context.get('share', 'IPC$')
            cmd = f"smbclient //{target}/{share} -N -c 'ls'"
            return cmd
        
        return None
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse smbclient output into structured facts"""
        
        facts = {}
        
        # Parse share listing
        if 'Sharename' in output and 'Type' in output and 'Comment' in output:
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
        
        return facts
