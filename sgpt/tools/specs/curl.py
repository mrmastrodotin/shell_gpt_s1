"""
Curl Tool Implementation
HTTP client for web requests and API testing
"""

import re
from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase


class CurlTool(BaseTool):
    """Curl HTTP client"""
    
    spec = ToolSpec(
        name="curl",
        binary="curl",
        category=ToolCategory.WEB,
        phases=[RedTeamPhase.RECON, RedTeamPhase.ENUMERATION, RedTeamPhase.VULNERABILITY_SCAN],
        requires_root=False,
        destructive=False,
        network_active=True,
        description="HTTP client for web requests and API enumeration",
        safe_flags=[
            "-I",           # HEAD request
            "-L",           # Follow redirects
            "-s",           # Silent
            "-v",           # Verbose
            "-X",           # HTTP method
            "-H",           # Header
            "-A",           # User-agent
            "-k",           # Insecure SSL
            "--head",       # HEAD only
            "-o",           # Output file
        ]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate curl command based on intent"""
        
        if intent == "web_probe":
            # Check if web service is alive
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            # Find target with HTTP/HTTPS
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        protocol = "https" if "ssl" in service.lower() or port == 443 else "http"
                        return f"curl -I -L -k {protocol}://{ip}:{port}"
            
            return None
        
        elif intent == "web_headers":
            # Get HTTP headers
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        protocol = "https" if port == 443 else "http"
                        return f"curl -v -s -k {protocol}://{ip}:{port} -o /dev/null"
            
            return None
        
        elif intent == "web_get":
            # GET request to URL
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        protocol = "https" if port == 443 else "http"
                        return f"curl -L -k {protocol}://{ip}:{port}"
            
            return None
        
        elif intent == "api_test":
            # Test API endpoint
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            for target in targets:
                services = target.get("services", {})
                for port, service in services.items():
                    if "http" in service.lower():
                        ip = target["ip"]
                        protocol = "https" if port == 443 else "http"
                        return f"curl -s -k {protocol}://{ip}:{port}/api -H 'Accept: application/json'"
            
            return None
        
        return None
    
    def parse_output(self, output: str) -> dict:
        """Parse curl output to extract facts"""
        facts = {
            "hosts": [],
            "targets": [],
            "web_info": []
        }
        
        # Extract HTTP status code
        status_match = re.search(r'HTTP/[\d.]+\s+(\d+)', output)
        if status_match:
            status_code = status_match.group(1)
            facts["web_info"].append({"status_code": status_code})
        
        # Extract server header
        server_match = re.search(r'Server:\s*(.+)', output, re.IGNORECASE)
        if server_match:
            server = server_match.group(1).strip()
            facts["web_info"].append({"server": server})
        
        # Extract content-type
        content_type_match = re.search(r'Content-Type:\s*(.+)', output, re.IGNORECASE)
        if content_type_match:
            content_type = content_type_match.group(1).strip()
            facts["web_info"].append({"content_type": content_type})
        
        return facts
