"""
Propose Prompt - Tool Selection
Selects which tool and parameters to use (NOT generating raw commands)
"""

PROPOSE_SYSTEM_PROMPT = """You are a tool selector for a red-team agent.

Your role: Given an objective and available tools, select the BEST tool and action.

You do NOT generate commands directly - you select:
1. Which tool to use
2. What action/intent for that tool
3. Any specific parameters needed

The tool registry will generate the actual safe command.

Output MUST be valid JSON."""

def ProposePrompt(plan: dict, available_tools: list, facts: dict, auto_context: dict) -> tuple[str, str]:
    """
    Generate Propose prompt
    
    Returns: (system_prompt, user_prompt)
    """
    
    objective = plan.get("objective", "")
    intent = plan.get("intent", "")
    rationale = plan.get("rationale", "")
    
    # Format available tools
    tools_info = []
    for tool_spec in available_tools:
        tools_info.append(f"""
Tool: {tool_spec.name}
Binary: {tool_spec.binary}
Category: {tool_spec.category.value}
Description: {tool_spec.description}
Requires Root: {tool_spec.requires_root}
Destructive: {tool_spec.destructive}
""")
    
    tools_str = "\n---\n".join(tools_info) if tools_info else "No tools available"
    
    # Format context
    network_info = auto_context.get("network", {})
    subnet = network_info.get("subnet", "Unknown")
    
    # Format facts
    live_hosts = facts.get("live_hosts", [])
    targets = facts.get("targets", [])
    
    user_prompt = f"""OBJECTIVE: {objective}
SUGGESTED INTENT: {intent}
RATIONALE: {rationale}

NETWORK CONTEXT:
- Subnet: {subnet}

KNOWN FACTS:
- Live Hosts: {live_hosts}
- Detailed Targets: {len(targets)}

AVAILABLE TOOLS:
{tools_str}

Select the tool and action to achieve the objective.

**Important:**
- Choose tool that matches the intent
- Tool must be in the available tools list
- Specify any target IPs, ports, or parameters needed
- The tool will generate the safe command

Respond with ONLY this JSON structure:
{{
  "tool_name": "name of tool to use",
  "action": "specific action/intent for tool",
  "parameters": {{
    "target": "IP or subnet if needed",
    "ports": "port list if needed",
    "flags": ["any", "specific", "flags"]
  }},
  "reasoning": "why this tool and action",
  "expected_outcome": "what we expect to discover"
}}

**Example:**
{{
  "tool_name": "nmap",
  "action": "host_discovery",
  "parameters": {{"target": "192.168.1.0/24"}},
  "reasoning": "No hosts discovered yet, start with network-wide ping scan",
  "expected_outcome": "List of live hosts on the network"
}}"""
    
    return (PROPOSE_SYSTEM_PROMPT, user_prompt)


PROPOSE_SCHEMA = {
    "type": "object",
    "required": ["tool_name", "action", "reasoning"],
    "properties": {
        "tool_name": {"type": "string"},
        "action": {"type": "string"},
        "parameters": {"type": "object"},
        "reasoning": {"type": "string"},
        "expected_outcome": {"type": "string"}
    }
}
