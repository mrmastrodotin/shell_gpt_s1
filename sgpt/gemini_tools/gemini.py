import os
import requests
from typing import List, Optional
from sgpt.config_manager import config_manager
from sgpt.credentials import get_api_key as get_cred_key

def get_gemini_api_key() -> Optional[str]:
    """
    Retrieves Gemini API key with priority:
    1. GOOGLE_API_KEY / GEMINI_API_KEY env var
    2. Credentials file (credentials.json)
    3. config.interfaces.gemini.api_key (Legacy)
    """
    # 1. Environment variables
    env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key
        
    # 2. Credentials file
    cred_key = get_cred_key("gemini")
    if cred_key:
        return cred_key

    # 3. Config (Legacy)
    try:
        gemini_config = config_manager.get_interface_config("gemini")
        if gemini_config and gemini_config.get("api_key"):
            return gemini_config.get("api_key")
    except Exception:
        pass

    return None

def fetch_gemini_models(api_key: str) -> List[dict]:
    """
    Fetches available models from Gemini API matching 'generateContent'.
    Returns list of dicts with name, input_tokens, output_tokens.
    """
    # Using v1 as per user recommendation (stable)
    url = "https://generativelanguage.googleapis.com/v1/models"
    params = {"key": api_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        models = data.get("models", [])
        usable = []

        for m in models:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                # User logic: Parse limits
                name = m.get("name", "").replace("models/", "")
                if name:
                    usable.append({
                        "name": name,
                        "input_tokens": m.get("inputTokenLimit"),
                        "output_tokens": m.get("outputTokenLimit")
                    })
        
        return sorted(usable, key=lambda x: x['name'])
    except Exception as e:
        raise e
