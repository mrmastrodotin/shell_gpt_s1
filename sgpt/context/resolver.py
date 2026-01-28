from sgpt.context.models import BehaviorRules

def resolve_behavior(prompt: str, defaults: BehaviorRules) -> BehaviorRules:
    """
    Overrides default behavior rules based on explicit user intent in the prompt.
    """
    prompt_lower = prompt.lower()
    
    # Clone defaults (dataclasses are mutable, but we create new instance to be safe)
    # Actually, let's just create a new instance initialized from defaults
    # or modify a copy.
    
    current = BehaviorRules(
        verbosity=defaults.verbosity,
        no_questions=defaults.no_questions,
        no_suggestions=defaults.no_suggestions,
        no_fluff=defaults.no_fluff,
        no_comparisons=defaults.no_comparisons
    )
    
    # Intent Detection
    if "explain" in prompt_lower:
        current.verbosity = "medium"
        current.no_fluff = False
        
    if "script" in prompt_lower or "code" in prompt_lower or "generate" in prompt_lower:
        current.verbosity = "code"
        
    if "suggest" in prompt_lower or "recommend" in prompt_lower:
        current.no_suggestions = False
        
    if "compare" in prompt_lower or "difference" in prompt_lower:
        current.no_comparisons = False
        
    return current
