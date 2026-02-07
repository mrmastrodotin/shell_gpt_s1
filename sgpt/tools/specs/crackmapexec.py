"""
CrackMapExec Tool
Network penetration testing and lateral movement
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class CrackMapExecTool(BaseTool):
    """CrackMapExec for SMB/WinRM exploitation"""
    
    spec = ToolSpec(
        name="crackmapexec",
        binary="crackmapexec",
        category=ToolCategory.EXPLOITATION,
        phases=[RedTeamPhase.ENUMERATION, RedTeamPhase.EXPLOITATION],
        requires_root=False,
        destructive=True,
        network_active=True,
        description="Network penetration testing tool",
        safe_flags=["smb", "-u", "-p", "--shares"]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate crackmapexec command"""
        
        target = None
        if facts.get('live_hosts'):
            target = facts['live_hosts'][0]
        elif context.get('network', {}).get('subnet'):
            target = context['network']['subnet']
            
        if not target:
            return None
            
        # Default credentials
        username = "admin"
        password = "password123"
        
        # Check facts for credentials
        if facts.get('credentials'):
             for cred in facts['credentials']:
                username = cred.get('username', username)
                password = cred.get('password', password)
                break
        
        if intent == "smb_enumeration":
            return f"crackmapexec smb {target}"
        
        elif intent == "smb_login":
            return f"crackmapexec smb {target} -u {username} -p {password}"
        
        elif intent == "smb_shares":
            return f"crackmapexec smb {target} -u {username} -p {password} --shares"
        
        elif intent == "execute_command":
            command = "whoami"
            return f"crackmapexec smb {target} -u {username} -p {password} -x '{command}'"
        
        return None
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse crackmapexec output into structured facts"""
        
        facts = {}
        
        # Hosts/OS
        if 'SMB' in output and '445' in output:
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
        
        # Authentication
        if '[+]' in output or 'Pwn3d!' in output:
             facts['authenticated'] = True
             if 'Pwn3d!' in output:
                 facts['admin_access'] = True

        # Shares
        if 'READ' in output or 'WRITE' in output:
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
                        
        # Command output
        if 'executed command' in output.lower():
             facts['command_output'] = output
             facts['success'] = 'error' not in output.lower()
        
        return facts
