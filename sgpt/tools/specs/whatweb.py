"""
WhatWeb Tool
Web technology fingerprinting and detection
"""

from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase
from typing import Dict, Any


class WhatWebTool(BaseTool):
    """Web technology detection using WhatWeb"""
    
    spec = ToolSpec(
        name="whatweb",
        binary="whatweb",
        category=ToolCategory.ENUMERATION,
        phases=[RedTeamPhase.ENUMERATION, RedTeamPhase.VULNERABILITY_SCAN],
        requires_root=False,
        destructive=False,
        description="Web technology fingerprinting and detection"
    )
    
    intents = [
        "web_fingerprint",     # Detect web technologies
        "tech_detection",      # Detailed tech stack detection
        "aggressive_scan"      # Aggressive fingerprinting
    ]
    
    def generate_command(self, intent: str, context: Dict, facts: Dict) -> str:
        """Generate whatweb command"""
        
        # Get target URL
        url = self._get_web_target(context, facts)
        if not url:
            return None
        
        if intent == "web_fingerprint":
            # Basic fingerprinting
            return f"whatweb {url}"
        
        elif intent == "tech_detection":
            # Verbose detection
            return f"whatweb -v {url}"
        
        elif intent == "aggressive_scan":
            # Aggressive mode
            return f"whatweb -a 3 {url}"
        
        return None
    
    def _get_web_target(self, context: Dict, facts: Dict) -> str:
        """Get web target URL"""
        
        # Check context
        if "url" in context:
            return context["url"]
        
        if "target" in context:
            target = context["target"]
            # Add http:// if not present
            if not target.startswith("http"):
                return f"http://{target}"
            return target
        
        # Check facts for web services
        if "targets" in facts:
            for target in facts["targets"]:
                services = target.get("services", {})
                
                # Look for HTTP ports
                for port, service in services.items():
                    port_num = int(port) if isinstance(port, str) else port
                    
                    if port_num in [80, 8080, 8000]:
                        return f"http://{target['ip']}:{port_num}"
                    elif port_num == 443:
                        return f"https://{target['ip']}:{port_num}"
                    elif "http" in service.lower():
                        protocol = "https" if "ssl" in service.lower() or port_num == 443 else "http"
                        return f"{protocol}://{target['ip']}:{port_num}"
        
        return None
    
    def parse_output(self, output: str) -> Dict:
        """Parse whatweb output"""
        
        facts = {
            "technologies": [],
            "server": None,
            "cms": None,
            "frameworks": [],
            "languages": []
        }
        
        # WhatWeb output format:
        # http://target [200 OK] Apache[2.4.41], PHP[7.4.3], WordPress[5.8]
        
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            # Parse technologies
            if '[' in line and ']' in line:
                # Extract all tech[version] patterns
                import re
                
                # Find all patterns like: Technology[version]
                pattern = r'(\w+)\[([^\]]*)\]'
                matches = re.findall(pattern, line)
                
                for tech, version in matches:
                    tech_info = {
                        "name": tech,
                        "version": version if version else "unknown"
                    }
                    
                    # Categorize
                    if tech.lower() in ['apache', 'nginx', 'iis', 'lighttpd']:
                        facts["server"] = f"{tech} {version}".strip()
                    
                    elif tech.lower() in ['wordpress', 'joomla', 'drupal']:
                        facts["cms"] = f"{tech} {version}".strip()
                    
                    elif tech.lower() in ['php', 'python', 'ruby', 'asp.net']:
                        facts["languages"].append(tech_info)
                    
                    elif tech.lower() in ['jquery', 'bootstrap', 'react', 'vue', 'angular']:
                        facts["frameworks"].append(tech_info)
                    
                    facts["technologies"].append(tech_info)
        
        return facts


# Register tool
def register():
    from sgpt.tools.registry import ToolRegistry
    return WhatWebTool()
