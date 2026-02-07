
from openai import OpenAI
import os
from typing import List

def list_openai_models(api_key: str = None) -> List[str]:
    """
    Lists available OpenAI models capable of chat/text.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set.")

    # Using client as per user example
    client = OpenAI(api_key=api_key)
    
    models = client.models.list()
    usable = []

    for m in models.data:
        # filter only chat / text-capable models
        # User logic: "gpt" or "o"
        if any(k in m.id for k in ["gpt", "o"]):
            usable.append(m.id)

    return sorted(usable)
