"""
Plan Prompt - Objective Decision
Decides what objective to pursue next
"""

PLAN_SYSTEM_PROMPT = """You are a tactical planner for a red-team penetration testing agent.

Your role: Given the analysis, decide the specific next objective to pursue.

Consider:
- Current phase constraints (recon → enumeration → vuln_scan → exploitation → post_exploitation)
- Available information (facts)
- Logical progression of a penetration test
- Safety and ethics (never destructive actions without explicit approval)

Output MUST be valid JSON."""

def PlanPrompt(reasoning: dict, phase: str, facts: dict, goal: str) -> tuple[str, str]:
    """
    Generate Plan prompt
    
    Returns: (system_prompt, user_prompt)
    """
    
    recommended_action = reasoning.get("recommended_next_action", "")
    should_transition = reasoning.get("should_transition_phase", False)
    confidence = reasoning.get("confidence", "medium")
    
    # Format available facts
    live_hosts = facts.get("live_hosts", [])
    targets = facts.get("targets", [])
    
    facts_summary = f"""
- {len(live_hosts)} live hosts discovered
- {len(targets)} targets with detailed information
- {sum(len(t.get('ports', [])) for t in targets)} total open ports found
"""
    
    user_prompt = f"""GOAL: {goal}
CURRENT PHASE: {phase}

REASONING ANALYSIS:
{reasoning.get('reasoning', 'N/A')}

RECOMMENDED ACTION: {recommended_action}
CONFIDENCE: {confidence}
SHOULD TRANSITION: {should_transition}

AVAILABLE FACTS:
{facts_summary}

Based on this analysis, decide the next objective.

**Phase Transitions:**
- RECON: Discover live hosts → move to ENUMERATION when hosts found
- ENUMERATION: Scan ports, detect services → move to VULNERABILITY_SCAN when services mapped
- VULNERABILITY_SCAN: Identify vulnerabilities → move to EXPLOITATION if vulns found
- EXPLOITATION: Attempt exploitation → move to POST_EXPLOITATION if access gained
- POST_EXPLOITATION: Maintain access, exfiltrate data → REPORTING when complete

**Red-Team Best Practices:**
- Start broad (network scan) then narrow (specific ports)
- Always enumerate before exploiting
- Document everything for reporting

Respond with ONLY this JSON structure:
{{
  "objective": "clear, specific objective to achieve",
  "intent": "tool_action_name",
  "should_transition": boolean,
  "next_phase": "phase_name" or null,
  "transition_reason": "why transition" or null,
  "priority": "high" | "medium" | "low",
  "rationale": "why this objective makes sense now"
}}

**Intent Examples:**
- "host_discovery" - Find live hosts on network
- "port_scan_quick" - Quick port scan on known hosts
- "port_scan_full" - Full port scan
- "service_detection" - Identify services on open ports
- "os_detection" - Fingerprint operating system
- "web_enum" - Enumerate web application
- "vuln_scan" - Scan for vulnerabilities"""
    
    return (PLAN_SYSTEM_PROMPT, user_prompt)


PLAN_SCHEMA = {
    "type": "object",
    "required": ["objective", "intent", "should_transition"],
    "properties": {
        "objective": {"type": "string"},
        "intent": {"type": "string"},
        "should_transition": {"type": "boolean"},
        "next_phase": {"type": ["string", "null"]},
        "transition_reason": {"type": ["string", "null"]},
        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
        "rationale": {"type": "string"}
    }
}
