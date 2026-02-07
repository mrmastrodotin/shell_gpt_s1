"""
Safety Validator Module
Enhanced safety validation for commands
"""

import re
from typing import Tuple


class SafetyValidator:
    """Validates commands for safety before execution"""
    
    # Destructive command patterns
    DESTRUCTIVE_PATTERNS = [
        r'\brm\s+-rf\b',                    # rm -rf
        r'\brm\s+.*\*',                     # rm with wildcard
        r'\bformat\b',                      # format command
        r'\bdel\s+/[fFsS]',                 # Windows del with force
        r'\bshutdown\b',                    # System shutdown
        r'\breboot\b',                      # System reboot
        r'\bmkfs\b',                        # Make filesystem
        r'\bdd\s+if=.*of=/dev/',            # dd to device
        r'>\s*/dev/sd[a-z]',                # Write to disk
        r'\bmv\s+.*\s+/dev/null',           # Move to /dev/null
        r'\bchmod\s+777',                   # Overly permissive
        r'\bchmod\s+-R\s+777',              # Recursive 777
        r'wget.*\|\s*bash',                 # Pipe wget to bash
        r'curl.*\|\s*bash',                 # Pipe curl to bash
    ]
    
    # Privilege escalation patterns
    PRIVESC_PATTERNS = [
        r'\bsudo\s+',                       # sudo
        r'\bsu\s+',                         # su
        r'\brunas\b',                       # Windows runas
        r'chmod\s+\+s\b',                   # Set SUID
        r'chown\s+root',                    # Change owner to root
    ]
    
    # Data exfiltration patterns (require approval)
    EXFIL_PATTERNS = [
        r'scp\s+.*@',                       # SCP to remote
        r'rsync\s+.*@',                     # Rsync to remote
        r'curl.*-X\s+POST\s+.*-d',          # POST with data
        r'nc\s+.*>',                        # Netcat output redirection
    ]
    
    # Known safe tool binaries
    SAFE_TOOLS = [
        'nmap', 'masscan', 'arp-scan', 'netdiscover',
        'nikto', 'gobuster', 'ffuf', 'dirb',
        'curl', 'wget', 'whois', 'dig', 'nslookup',
        'enum4linux', 'smbclient', 'ldapsearch',
        'python', 'python3', 'bash', 'sh',
        'grep', 'sed', 'awk', 'cat', 'less',
        'find', 'locate', 'which',
    ]
    
    @staticmethod
    def validate(command: str) -> Tuple[bool, str]:
        """
        Validate command for safety
        
        Returns:
            (is_safe: bool, reason: str)
        """
        
        # Check for destructive patterns
        for pattern in SafetyValidator.DESTRUCTIVE_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return (False, f"Destructive command detected: {pattern}")
        
        # Check for privilege escalation
        for pattern in SafetyValidator.PRIVESC_PATTERNS:
            if re.search(pattern, command):
                return (False, f"Privilege escalation detected: {pattern}")
        
        # Extract binary name
        binary = command.split()[0] if command.split() else ""
        binary = binary.split('/')[-1]  # Handle full paths
        
        # Warn if binary not in safe list
        if binary and binary not in SafetyValidator.SAFE_TOOLS:
            # Not blocking, but flagging
            pass  # Could log warning
        
        # Check for suspicious flag combinations
        if '-e' in command and 'sh' in command:
            # Could be command execution
            return (False, "Suspicious command execution pattern")
        
        # Check for pipe to interpreter
        if re.search(r'\|\s*(bash|sh|python|perl|ruby)', command):
            return (False, "Piping to interpreter detected")
        
        return (True, "Command passed safety checks")
    
    @staticmethod
    def requires_approval(command: str) -> Tuple[bool, str]:
        """
        Check if command requires explicit approval
        
        Returns:
            (requires_approval: bool, reason: str)
        """
        
        # Check for data exfiltration
        for pattern in SafetyValidator.EXFIL_PATTERNS:
            if re.search(pattern, command):
                return (True, f"Data exfiltration pattern detected: {pattern}")
        
        # Check for writes to important files
        important_paths = ['/etc/', '/var/', '/usr/', '/sys/', 'C:\\Windows', 'C:\\Program Files']
        if '>' in command or '>>' in command:
            for path in important_paths:
                if path in command:
                    return (True, f"Writing to important directory: {path}")
        
        return (False, "No special approval needed")
    
    @staticmethod
    def sanitize(command: str) -> str:
        """
        Sanitize command by removing dangerous elements
        
        Returns:
            Sanitized command
        """
        
        # Remove trailing &&, ||, ; to prevent chaining
        sanitized = re.sub(r'[;&|]+\s*$', '', command)
        
        # Remove leading sudo/su
        sanitized = re.sub(r'^\s*(sudo|su)\s+', '', sanitized)
        
        return sanitized.strip()
