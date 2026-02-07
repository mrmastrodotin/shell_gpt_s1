from sgpt.context.models import AutoContext

def render_context(context: AutoContext) -> str:
    """
    Renders the AutoContext object into a structured system message block.
    """
    lines = []
    lines.append("SYSTEM CONTEXT (do not repeat)")
    lines.append("")
    
    # Environment
    lines.append("Environment:")
    sys = context.system
    lines.append(f"- {sys.os} ({sys.distro}), kernel {sys.kernel}, {sys.privilege}")
    lines.append(f"- User: {sys.user}")
    if context.network.ip and context.network.ip != "127.0.0.1":
        lines.append(f"- Network: {context.network.ip}, Interface: {context.network.interface}")
    lines.append("")
    
    # Tools
    available_tools = [t for t, avail in context.tools.items() if avail]
    missing_tools = [t for t, avail in context.tools.items() if not avail]
    
    lines.append("Tools available:")
    if available_tools:
        lines.append(f"- {', '.join(available_tools)}")
    else:
        lines.append("- None detected")
        
    if missing_tools:
        # Maybe concise? "hydra NOT available"
        # Let's list only if critical? Or just list unavailable as user requested.
        # User example: "- hydra NOT available"
        lines.append(f"- NOT available: {', '.join(missing_tools)}")
    lines.append("")
    
    # Session
    if context.session.commands:
        lines.append("Session facts:")
        for record in context.session.commands[-5:]: # Limit to last 5 to reduce noise?
            lines.append(f"- Ran `{record.command}`: {record.summary}")
    else:
        lines.append("Session facts:")
        lines.append("- New session started")
    lines.append("")
    
    lines.append("Behavior:")
    lines.append(f"- Verbosity: {beh.verbosity}")
    if beh.no_questions: lines.append("- No questions")
    if beh.no_suggestions: lines.append("- No suggestions")
    if beh.no_fluff: lines.append("- Be concise, internal monologue forbidden")
    
    lines.append(f"IMPORTANT: The current user is '{sys.user}'. Address them by name if the interaction allows.")
    
    return "\n".join(lines)
