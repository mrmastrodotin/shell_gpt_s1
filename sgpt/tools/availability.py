"""
Tool Availability Checker
Detects which tools are installed and available on the system
"""

import subprocess
import shutil
from typing import Dict, List
from pathlib import Path


class ToolAvailabilityChecker:
    """Check which tools are installed on the system"""
    
    @staticmethod
    def check_binary(binary: str) -> bool:
        """
        Check if a binary is available on the system
        
        Returns:
            True if binary is found, False otherwise
        """
        # Use shutil.which to check PATH
        if shutil.which(binary):
            return True
        
        # For Windows, also check common installation paths
        if shutil.which(binary + ".exe"):
            return True
        
        return False
    
    @staticmethod
    def check_all(tool_registry) -> Dict[str, bool]:
        """
        Check availability of all tools in registry
        
        Returns:
            Dict mapping binary name to availability status
        """
        availability = {}
        
        # Load tools if not already loaded
        tool_registry.load_tools()
        
        # Check each tool
        for tool_name, tool in tool_registry._tools.items():
            binary = tool.spec.binary
            is_available = ToolAvailabilityChecker.check_binary(binary)
            availability[binary] = is_available
        
        return availability
    
    @staticmethod
    def get_version(binary: str) -> str:
        """
        Get version of a tool
        
        Returns:
            Version string or "unknown"
        """
        version_flags = ["--version", "-v", "-V", "version"]
        
        for flag in version_flags:
            try:
                result = subprocess.run(
                    [binary, flag],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Return first line of version output
                    return result.stdout.split('\n')[0].strip()
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                continue
        
        return "unknown"
    
    @staticmethod
    def generate_report(tool_registry) -> str:
        """
        Generate availability report
        
        Returns:
            Formatted report string
        """
        availability = ToolAvailabilityChecker.check_all(tool_registry)
        
        report_lines = [
            "Tool Availability Report",
            "=" * 60,
            ""
        ]
        
        available = []
        unavailable = []
        
        for binary, is_available in sorted(availability.items()):
            if is_available:
                version = ToolAvailabilityChecker.get_version(binary)
                available.append(f"✅ {binary:20s} {version}")
            else:
                unavailable.append(f"❌ {binary:20s} NOT FOUND")
        
        if available:
            report_lines.append("Available Tools:")
            report_lines.extend(available)
            report_lines.append("")
        
        if unavailable:
            report_lines.append("Missing Tools:")
            report_lines.extend(unavailable)
            report_lines.append("")
        
        report_lines.append(f"Total: {len(available)}/{len(availability)} tools available")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    @staticmethod
    def install_suggestions(unavailable_tools: List[str]) -> Dict[str, str]:
        """
        Provide installation suggestions for missing tools
        
        Returns:
            Dict mapping tool name to installation command
        """
        suggestions = {
            "nmap": "apt install nmap  # or: brew install nmap",
            "curl": "apt install curl  # or: brew install curl",
            "gobuster": "apt install gobuster  # or: go install github.com/OJ/gobuster/v3@latest",
            "nikto": "apt install nikto  # or: git clone https://github.com/sullo/nikto.git",
            "python": "Built-in on most systems",
            "python3": "apt install python3  # or: brew install python3",
            "enum4linux": "apt install enum4linux  # or: git clone https://github.com/CiscoCXSecurity/enum4linux.git",
            "smbclient": "apt install smbclient  # or: brew install samba",
        }
        
        return {tool: suggestions.get(tool, "Manual installation required") for tool in unavailable_tools}
