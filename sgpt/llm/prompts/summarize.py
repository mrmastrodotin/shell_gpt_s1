"""
Summarize Prompt - Fact Extraction
Extracts structured facts from command output
"""

SUMMARIZE_SYSTEM_PROMPT = """You are a fact extraction engine for red-team operations.

Your role: Parse command output and extract ONLY concrete, verifiable facts.

Rules:
- Extract IPs, ports, services, versions, OS info
- Do NOT make assumptions or inferences
- Do NOT include opinions
- stick to what the output explicitly shows

Output MUST be valid JSON."""

def SummarizePrompt(command: str, output: str, tool_name: str) -> tuple[str, str]:
    """
    Generate Summarize prompt
    
    Returns: (system_prompt, user_prompt)
    """
    
    user_prompt = f"""TOOL USED: {tool_name}
COMMAND: {command}

OUTPUT:
{output[:2000]}  

Extract all facts from this output.

**Fact Categories:**
- Hosts: IP addresses that are live/responsive
- Ports: Open ports on specific hosts
- Services: Service names/versions running on ports
- OS: Operating system fingerprints
- Vulnerabilities: Any CVEs or security issues identified
- Other: Anything else concrete and useful

Respond with ONLY this JSON structure:
{{
  "hosts": ["192.168.1.1", "192.168.1.10"],
  "targets": [
    {{
      "ip": "192.168.1.10",
      "ports": [22, 80, 443],
      "services": {{
        "22": "OpenSSH 8.2",
        "80": "Apache httpd 2.4.41",
        "443": "Apache httpd 2.4.41"
      }},
      "os": "Linux 5.4",
      "hostname": "webserver.local"
    }}
  ],
  "vulnerabilities": [
    {{
      "cve_id": "CVE-2021-XXXX",
      "target": "192.168.1.10",
      "port": 22,
      "severity": "high",
      "description": "SSH vulnerability"
    }}
  ],
  "summary": "Brief human-readable summary of what was discovered",
  "success": true,
  "error_message": null
}}

If no facts found, return empty arrays but still include "success" and "summary" fields."""
    
    return (SUMMARIZE_SYSTEM_PROMPT, user_prompt)


SUMMARIZE_SCHEMA = {
    "type": "object",
    "required": ["success", "summary"],
    "properties": {
        "hosts": {"type": "array", "items": {"type": "string"}},
        "targets": {"type": "array"},
        "vulnerabilities": {"type": "array"},
        "summary": {"type": "string"},
        "success": {"type": "boolean"},
        "error_message": {"type": ["string", "null"]}
    }
}
