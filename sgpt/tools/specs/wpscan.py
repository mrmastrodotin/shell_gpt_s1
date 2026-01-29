"""
WPScan Tool
WordPress vulnerability scanner
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class WPScanTool(BaseTool):
    """WPScan for WordPress security testing"""
    
    def __init__(self):
        super().__init__(
            name="wpscan",
            category=ToolCategory.VULNERABILITY,
            intents=[
                "enumerate_wordpress",
                "enumerate_users",
                "enumerate_plugins",
                "password_attack"
            ]
        )
    
    def get_spec(self, intent: str) -> ToolSpec:
        """Get tool specification for given intent"""
        
        specs = {
            "enumerate_wordpress": ToolSpec(
                description="Enumerate WordPress version and basic info",
                parameters={
                    "url": "WordPress site URL",
                    "api_token": "WPScan API token (optional)"
                },
                example="wpscan --url https://example.com",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "enumerate_users": ToolSpec(
                description="Enumerate WordPress users",
                parameters={
                    "url": "WordPress site URL"
                },
                example="wpscan --url https://example.com --enumerate u",
                phase=RedTeamPhase.ENUMERATION,
                risk_level="low"
            ),
            
            "enumerate_plugins": ToolSpec(
                description="Enumerate installed plugins and check for vulnerabilities",
                parameters={
                    "url": "WordPress site URL",
                    "api_token": "WPScan API token (optional)"
                },
                example="wpscan --url https://example.com --enumerate p",
                phase=RedTeamPhase.VULNERABILITY,
                risk_level="low"
            ),
            
            "password_attack": ToolSpec(
                description="Brute force WordPress login",
                parameters={
                    "url": "WordPress site URL",
                    "usernames": "Username or username list file",
                    "passwords": "Password list file"
                },
                example="wpscan --url https://example.com -U admin -P /usr/share/wordlists/rockyou.txt",
                phase=RedTeamPhase.EXPLOITATION,
                risk_level="high"
            )
        }
        
        return specs.get(intent)
    
    def build_command(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Build wpscan command"""
        
        url = parameters.get('url')
        
        if intent == "enumerate_wordpress":
            cmd = f"wpscan --url {url}"
            
            api_token = parameters.get('api_token')
            if api_token:
                cmd += f" --api-token {api_token}"
            
            return cmd
        
        elif intent == "enumerate_users":
            return f"wpscan --url {url} --enumerate u"
        
        elif intent == "enumerate_plugins":
            cmd = f"wpscan --url {url} --enumerate p"
            
            api_token = parameters.get('api_token')
            if api_token:
                cmd += f" --api-token {api_token}"
            
            return cmd
        
        elif intent == "password_attack":
            usernames = parameters.get('usernames')
            passwords = parameters.get('passwords')
            
            cmd = f"wpscan --url {url}"
            
            # Check if usernames is a file or single username
            if '/' in usernames or '\\' in usernames:
                cmd += f" -U {usernames}"
            else:
                cmd += f" -U {usernames}"
            
            cmd += f" -P {passwords}"
            
            return cmd
        
        return None
    
    def validate_parameters(self, intent: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters for intent"""
        
        if not parameters.get('url'):
            return False
        
        if intent == "password_attack":
            return 'usernames' in parameters and 'passwords' in parameters
        
        return True
    
    def parse_output(self, intent: str, output: str) -> Dict[str, Any]:
        """Parse wpscan output into structured facts"""
        
        facts = {}
        
        if intent == "enumerate_wordpress":
            # Extract WordPress version
            if 'WordPress version' in output:
                for line in output.split('\n'):
                    if 'WordPress version' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            facts['wp_version'] = parts[1].strip()
        
        elif intent == "enumerate_users":
            # Extract usernames
            facts['users'] = []
            lines = output.split('\n')
            
            for line in lines:
                if '[i] User(s) Identified:' in line:
                    # Next lines contain usernames
                    continue
                if line.strip().startswith('[+]'):
                    username = line.split('[+]')[1].strip().split()[0]
                    facts['users'].append(username)
        
        elif intent == "enumerate_plugins":
            # Extract vulnerable plugins
            facts['plugins'] = []
            facts['vulnerable_plugins'] = []
            
            # Parse plugin information
            in_plugin_section = False
            current_plugin = None
            
            for line in output.split('\n'):
                if '[+]' in line and 'plugin' in line.lower():
                    plugin_name = line.split('[+]')[1].strip()
                    facts['plugins'].append(plugin_name)
                    current_plugin = plugin_name
                
                if current_plugin and 'vulnerabilities' in line.lower():
                    facts['vulnerable_plugins'].append(current_plugin)
        
        elif intent == "password_attack":
            # Check for successful login
            facts['credentials'] = []
            
            if 'Valid Combinations Found:' in output or '[SUCCESS]' in output:
                for line in output.split('\n'):
                    if 'Username:' in line and 'Password:' in line:
                        facts['credentials'].append(line.strip())
        
        return facts
