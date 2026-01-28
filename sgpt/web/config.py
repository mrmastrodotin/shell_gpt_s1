from pathlib import Path
from sgpt.config import SHELL_GPT_CONFIG_FOLDER

WEB_CONFIG_DIR = SHELL_GPT_CONFIG_FOLDER / "web"
PROFILES_DIR = WEB_CONFIG_DIR / "profiles"

def get_profile_dir(provider: str) -> Path:
    path = PROFILES_DIR / provider
    path.mkdir(parents=True, exist_ok=True)
    return path
