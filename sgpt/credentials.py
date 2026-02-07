
import json
import os
from pathlib import Path
from typing import Dict, Optional
from sgpt.config import SHELL_GPT_CONFIG_FOLDER

CREDENTIALS_PATH = SHELL_GPT_CONFIG_FOLDER / "credentials.json"

try:
    import keyring
except ImportError:
    keyring = None

SERVICE_NAME = "shell_gpt"

def get_credentials() -> Dict[str, Dict[str, str]]:
    """
    Load credentials from JSON file.
    Returns empty dict if file doesn't exist or is invalid.
    """
    if not CREDENTIALS_PATH.exists():
        return {}
    
    try:
        with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

def save_credentials(data: Dict[str, Dict[str, str]]) -> None:
    """
    Save credentials to JSON file with restricted permissions.
    """
    SHELL_GPT_CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
    
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    # Set permissions to 600 (owner read/write only) on non-Windows
    if os.name != "nt":
        try:
            os.chmod(CREDENTIALS_PATH, 0o600)
        except OSError:
            pass

def set_api_key(provider: str, key: str) -> None:
    """
    Save API key securely. Tries System Keyring first, falls back to JSON.
    """
    use_keyring = False
    if keyring:
        try:
            keyring.set_password(SERVICE_NAME, provider, key)
            use_keyring = True
        except Exception:
            pass # Keyring failed, fallback to file
            
    creds = get_credentials()
    if provider not in creds:
        creds[provider] = {}
        
    if use_keyring:
        # If saved to keyring, remove from file if it existed
        creds[provider].pop("api_key", None)
        creds[provider]["storage"] = "keyring"
    else:
        # Fallback to file
        creds[provider]["api_key"] = key
        creds[provider]["storage"] = "file"
        
    save_credentials(creds)

def get_api_key(provider: str) -> Optional[str]:
    """
    Helper to get API key for a specific provider.
    Priority: Keyring -> File
    """
    # 1. Try Keyring
    if keyring:
        try:
            key = keyring.get_password(SERVICE_NAME, provider)
            if key:
                return key
        except Exception:
            pass

    # 2. Try File
    creds = get_credentials()
    return creds.get(provider, {}).get("api_key")

def delete_api_key(provider: str) -> bool:
    """
    Delete API key for a provider from both keyring and file.
    Returns True if key was found and deleted, False otherwise.
    """
    deleted = False
    
    # 1. Delete from Keyring
    if keyring:
        try:
            keyring.delete_password(SERVICE_NAME, provider)
            deleted = True
        except Exception:
            pass  # Key might not exist in keyring
    
    # 2. Delete from File
    creds = get_credentials()
    if provider in creds:
        creds.pop(provider)
        save_credentials(creds)
        deleted = True
    
    return deleted

