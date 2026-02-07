"""
Think Prompt - Internal Reasoning
Hidden from user, analyzes current state and decides next steps
"""

THINK_SYSTEM_PROMPT = """You are a strategic reasoning engine for a red-team automation agent.

Your role: Analyze the current state and determine what should happen next.

You are NOT making decisions - only analyzing the situation.

Output MUST be valid JSON."""

def ThinkPrompt(observation: dict) -> tuple[str, str]:
    """
    Generate Think prompt
    
    Returns: (system_prompt, user_prompt)
    """
    
    goal = observation.get("goal", "")
    phase = observation.get("phase", "")
    facts = observation.get("facts", {})
    last_command = observation.get("last_command")
    total_commands = observation.get("total_commands", 0)
    failures = observation.get("failures", 0)
    
    # Format facts for display
    live_hosts = facts.get("live_hosts", [])
    targets = facts.get("targets", [])
    vulnerabilities = facts.get("vulnerabilities", [])
    
    facts_summary = f"""
Live Hosts: {len(live_hosts)} ({', '.join(live_hosts[:5])}{'...' if len(live_hosts) > 5 else ''})
Detailed Targets: {len(targets)}
Vulnerabilities: {len(vulnerabilities)}
"""
    
    # Format last command
    last_cmd_info = "None yet"
    if last_command:
        last_cmd_info = f"""
Command: {last_command.get('command', 'N/A')}
Exit Code: {last_command.get('exit_code', 'N/A')}
Output Preview: {last_command.get('output', '')[:200]}...
Facts Extracted: {len(last_command.get('facts_extracted', {}))} items
"""
    
    user_prompt = f"""GOAL: {goal}
CURRENT PHASE: {phase}
TOTAL COMMANDS EXECUTED: {total_commands}
TOTAL FAILURES: {failures}

KNOWN FACTS:
{facts_summary}

LAST COMMAND:
{last_cmd_info}

Analyze the situation and answer:

1. **Is the goal satisfied?** 
   - Has the objective been fully achieved?
   
2. **Was the last command successful?**
   - Did it produce useful information?
   - Did it fail or error?
   
3. **What new facts were discovered?**
   - List key discoveries from last command
   
4. **Should we transition to a new phase?**
   - Are we done with current phase?
   - What phase should we move to?
   
5. **What logical next action achieves the goal?**
   - Based on what we know, what should happen next?

Respond with ONLY this JSON structure:
{{
  "goal_satisfied": boolean,
  "last_command_success": boolean,
  "new_facts_discovered": ["fact1", "fact2"],
  "should_transition_phase": boolean,
  "next_phase": "phase_name" or null,
  "transition_reason": "why transition" or null,
  "recommended_next_action": "specific action description",
  "confidence": "high" | "medium" | "low",
  "reasoning": "brief explanation of analysis"
}}"""
    
    return (THINK_SYSTEM_PROMPT, user_prompt)


# JSON schema for validation
THINK_SCHEMA = {
    "type": "object",
    "required": ["goal_satisfied", "last_command_success", "new_facts_discovered", 
                 "should_transition_phase", "recommended_next_action"],
    "properties": {
        "goal_satisfied": {"type": "boolean"},
        "last_command_success": {"type": "boolean"},
        "new_facts_discovered": {"type": "array", "items": {"type": "string"}},
        "should_transition_phase": {"type": "boolean"},
        "next_phase": {"type": ["string", "null"]},
        "transition_reason": {"type": ["string", "null"]},
        "recommended_next_action": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "reasoning": {"type": "string"}
    }
}
