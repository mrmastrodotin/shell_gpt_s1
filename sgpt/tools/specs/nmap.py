"""
Nmap Tool Implementation
Network discovery and port scanning
"""

import re
from sgpt.tools.registry import BaseTool, ToolSpec, ToolCategory
from sgpt.agent.state import RedTeamPhase, Target


class NmapTool(BaseTool):
    """Nmap network scanner"""
    
    spec = ToolSpec(
        name="nmap",
        binary="nmap",
        category=ToolCategory.DISCOVERY,
        phases=[RedTeamPhase.RECON, RedTeamPhase.ENUMERATION],
        requires_root=True,
        destructive=False,
        network_active=True,
        description="Network discovery and port scanning",
        safe_flags=[
            "-sn",      # Ping scan
            "-sS",      # SYN scan
            "-sT",      # TCP connect scan
            "-sV",      # Version detection
            "-p-",      # All ports
            "-p",       # Specific ports
            "--top-ports",
            "-O",       # OS detection
            "-A",       # Aggressive scan
            "-T4",      # Timing template
            "-Pn",      # No ping
            "-n",       # No DNS
        ]
    )
    
    def generate_command(
        self,
        intent: str,
        context: dict,
        facts: dict
    ) -> str:
        """Generate nmap command based on intent"""
        
        if intent == "host_discovery":
            # Ping scan to find live hosts
            subnet = context.get("network", {}).get("subnet", "192.168.0.0/24")
            return f"nmap -sn {subnet}"
        
        elif intent == "port_scan_quick":
            # Quick port scan on discovered hosts
            hosts = facts.get("live_hosts", [])
            if not hosts:
                return None
            
            target = hosts[0]  # Start with first host
            return f"nmap -sS --top-ports 100 {target}"
        
        elif intent == "port_scan_full":
            # Full port scan
            hosts = facts.get("live_hosts", [])
            if not hosts:
                return None
            
            target = hosts[0]
            return f"nmap -sS -p- {target}"
        
        elif intent == "service_detection":
            # Service version detection
            targets = facts.get("targets", [])
            if not targets:
                return None
            
            target_data = targets[0]
            ip = target_data["ip"]
            ports = target_data.get("ports", [])
            
            if not ports:
                return f"nmap -sV {ip}"
            
            port_list = ",".join(map(str, ports[:20]))  # Limit to first 20
            return f"nmap -sV -p {port_list} {ip}"
        
        elif intent == "os_detection":
            # OS fingerprinting
            hosts = facts.get("live_hosts", [])
            if not hosts:
                return None
            
            target = hosts[0]
            return f"nmap -O {target}"
        
        return None
    
    def parse_output(self, output: str) -> dict:
        """
        Parse nmap output to extract facts
        
        Returns dict with:
        - hosts: list of discovered IPs
        - targets: list of target dicts with ports/services
        """
        facts = {
            "hosts": [],
            "targets": []
        }
        
        # Parse host discovery (-sn)
        host_pattern = r"Nmap scan report for (?:[\w\.-]+ \()?(\d+\.\d+\.\d+\.\d+)"
        for match in re.finditer(host_pattern, output):
            ip = match.group(1)
            if ip not in facts["hosts"]:
                facts["hosts"].append(ip)
        
        # Parse open ports
        port_pattern = r"(\d+)/(tcp|udp)\s+open\s+([\w\-]+)"
        
        current_ip = None
        current_target = None
        
        for line in output.split("\n"):
            # Track current host
            host_match = re.search(host_pattern, line)
            if host_match:
                current_ip = host_match.group(1)
                current_target = {
                    "ip": current_ip,
                    "ports": [],
                    "services": {}
                }
            
            # Parse ports
            port_match = re.search(port_pattern, line)
            if port_match and current_target:
                port = int(port_match.group(1))
                service = port_match.group(3)
                
                current_target["ports"].append(port)
                current_target["services"][port] = service
        
        if current_target and current_target["ports"]:
            facts["targets"].append(current_target)
        
        return facts
