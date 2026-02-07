import platform
import os
import shutil
import socket
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sgpt.context.models import (
    SystemContext, NetworkContext, RuntimeContext, 
    BehaviorRules, SessionMemory, AutoContext
)

def run_cmd_output(cmd: List[str]) -> Optional[str]:
    """Runs a command and returns stripped output if successful, else None."""
    try:
        if not shutil.which(cmd[0]):
            return None
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None

def run_first_available(cmds_list: List[List[str]]) -> Optional[str]:
    """Runs the first available command from a list."""
    for cmd in cmds_list:
        out = run_cmd_output(cmd)
        if out is not None:
            return out
    return None

def get_linux_distro() -> str:
    """Portable Linux distro detection via /etc/os-release."""
    if not os.path.exists("/etc/os-release"):
        return "Linux"
    try:
        distro_id = "Linux"
        pretty_name = "Linux"
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    v = v.strip('"')
                    if k == "ID":
                        distro_id = v
                    elif k == "PRETTY_NAME":
                        pretty_name = v
        return pretty_name # Return pretty name e.g. "Kali Linux 2024.1"
    except Exception:
        return "Linux"

def build_system_context() -> SystemContext:
    uname = platform.uname()
    os_system = uname.system
    
    # Distro
    if os_system == "Linux":
        distro = get_linux_distro()
        # Privilege
        privilege = "root" if os.geteuid() == 0 else "user"
    elif os_system == "Windows":
        distro = f"Windows {uname.release}" 
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            privilege = "Administrator" if is_admin else "User"
        except:
            privilege = "Unknown"
    elif os_system == "Darwin":
        distro = f"macOS {uname.release}"
        privilege = "root" if os.geteuid() == 0 else "user"
    else:
        distro = "Unknown"
        privilege = "Unknown"

    shell = os.path.basename(os.environ.get("SHELL", os.environ.get("COMSPEC", "unknown")))
    user = os.getenv("USERNAME") or os.getenv("USER") or "unknown"

    return SystemContext(
        os=os_system,
        distro=distro,
        kernel=uname.release,
        arch=uname.machine,
        privilege=privilege,
        shell=shell,
        user=user
    )

def parse_ip_subnet(output: str) -> Tuple[str, str]:
    """
    Parses IP string from command output.
    Very basic heuristic for now, better than hardcoding.
    """
    # Regex for IPv4 with CIDR
    # This is a simplification.
    # Look for "inet 192.168.x.x/24" pattern common in `ip addr`
    match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+/\d+)", output)
    if match:
        cidr = match.group(1)
        ip = cidr.split("/")[0]
        # Calculate subnet is complex without `ipaddress` module, 
        # but user just wants the string context.
        return ip, cidr # CIDR acts as subnet context
    
    # Fallback for ifconfig: "inet 192.168.x.x netmask ..."
    match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", output)
    if match:
        return match.group(1), "unknown"
        
    return "127.0.0.1", "unknown"

def build_network_context() -> NetworkContext:
    os_system = platform.system()
    
    ip = "127.0.0.1"
    subnet = "unknown"
    interface = "unknown"
    
    if os_system == "Linux" or os_system == "Darwin":
        # Try ip, then ifconfig
        out = run_first_available([
            ["ip", "-4", "addr", "show"], # Linux
            ["ifconfig"]     # macOS / Legacy Linux
        ])
        if out:
            # Parse output
            # We want the primary non-loopback.
            # This logic mimics "passive" detection.
            # We don't want to parse 100 lines.
            # Heuristic: First inet that is NOT 127.0.0.1
            ips = re.findall(r"inet\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?", out)
            for found_ip, found_cidr in ips:
                if not found_ip.startswith("127."):
                    ip = found_ip
                    if found_cidr:
                        subnet = f"{found_ip}/{found_cidr}"
                    else:
                         # Try to find netmask in same line or context?
                         # Too complex for regex.
                         subnet = "unknown"
                    interface = "detected" # Parsing interface name requires more logic
                    break

    elif os_system == "Windows":
        # ipconfig
        out = run_cmd_output(["ipconfig"])
        if out:
             # Parse IPv4 Address. . . . . . . . . . . : 192.168.1.10
             match = re.search(r"IPv4 Address[ .]+: (\d+\.\d+\.\d+\.\d+)", out)
             if match:
                 ip = match.group(1)
                 interface = "primary"
                 # Subnet mask line follows usually
                 match_mask = re.search(r"Subnet Mask[ .]+: (\d+\.\d+\.\d+\.\d+)", out)
                 if match_mask:
                     subnet = match_mask.group(1)

    return NetworkContext(
        interface=interface,
        ip=ip,
        subnet=subnet,
        default_route="unknown", # Parsing route is harder, skip for now to keep noise low
        environment="unknown"
    )

def build_tool_context() -> Dict[str, bool]:
    tools = [
        "nmap", "tcpdump", "sqlmap", "hydra", 
        "curl", "wget", "git", "docker", 
        "python", "node", "kubectl", "ip", "ifconfig"
    ]
    return {tool: bool(shutil.which(tool)) for tool in tools}

def build_runtime_context() -> RuntimeContext:
    return RuntimeContext(
        cwd=os.getcwd()
    )

def initialize_session_memory() -> SessionMemory:
    return SessionMemory(
        started_at=datetime.now(),
        commands=[]
    )

def build_context() -> AutoContext:
    return AutoContext(
        system=build_system_context(),
        network=build_network_context(),
        tools=build_tool_context(),
        runtime=build_runtime_context(),
        behavior=BehaviorRules(),
        session=initialize_session_memory()
    )
