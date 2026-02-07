"""
SQLMap Tool
Automated SQL injection detection and exploitation
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class SQLMapTool(BaseTool):
    """SQLMap for SQL injection testing"""
    
    spec = ToolSpec(
        name="sqlmap",
        binary="sqlmap",
        category=ToolCategory.EXPLOITATION,
        phases=[RedTeamPhase.VULNERABILITY, RedTeamPhase.EXPLOITATION],
        requires_root=False,
        destructive=True,
        network_active=True,
        description="Automated SQL injection detection and exploitation",
        safe_flags=["-u", "--batch", "--dbs", "--tables"]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate sqlmap command"""
        
        # Extract URL
        url = None
        if context.get('url'):
            url = context['url']
        elif facts.get('target_url'):
            url = facts['target_url']
            
        if not url:
            return None
            
        if intent == "test_injection":
            cmd = f"sqlmap -u '{url}' --batch --level=1 --risk=1"
            return cmd
        
        elif intent == "enumerate_databases":
            cmd = f"sqlmap -u '{url}' --dbs --batch"
            return cmd
        
        elif intent == "dump_tables":
            database = "users" # Default guess
            cmd = f"sqlmap -u '{url}' -D {database} --dump-all --batch"
            return cmd
        
        elif intent == "command_execution":
            command = "whoami"
            return f"sqlmap -u '{url}' --os-cmd='{command}' --batch"
        
        return None
    
    
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse sqlmap output into structured facts"""
        
        facts = {}
        
        # Check for injection
        if 'is vulnerable' in output.lower() or 'sqlmap identified' in output.lower():
            facts['vulnerable'] = True
            facts['injection_type'] = []
            
            if 'boolean-based blind' in output:
                facts['injection_type'].append('boolean-based blind')
            if 'time-based blind' in output:
                facts['injection_type'].append('time-based blind')
            if 'error-based' in output:
                facts['injection_type'].append('error-based')
            if 'UNION query' in output:
                facts['injection_type'].append('UNION query')
        
        # Database enumeration
        if 'available databases' in output.lower():
            facts['databases'] = []
            lines = output.split('\n')
            in_db_section = False
            
            for line in lines:
                if 'available databases' in line.lower():
                    in_db_section = True
                elif in_db_section and line.strip().startswith('[*]'):
                    db_name = line.strip()[3:].strip()
                    facts['databases'].append(db_name)
        
        return facts
