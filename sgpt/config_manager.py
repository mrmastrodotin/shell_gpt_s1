import json
import os
from pathlib import Path
from typing import Any, Dict

from sgpt.config import SHELL_GPT_CONFIG_FOLDER

INTERFACES_CONFIG_PATH = SHELL_GPT_CONFIG_FOLDER / "interfaces.json"

DEFAULT_INTERFACES_CONFIG = {
    "current": "openai",
    "interfaces": {
        "openai": {},
        "ollama": {
            "host": "http://localhost:11434",
            "model": "llama3"
        },
        "gemini": {
            "model": "gemini-1.5-flash",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": ""
        },
        "web": {
            "providers": {
                "chatgpt": "https://chatgpt.com",
                "gemini": "https://gemini.google.com",
                "claude": "https://claude.ai"
            },
            "default_provider": "chatgpt"
        },
        "web-automation": {
            "provider": "chatgpt"
        }
    }
}

class ConfigManager:
    def __init__(self, config_path: Path = INTERFACES_CONFIG_PATH):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            self._save_config(DEFAULT_INTERFACES_CONFIG)
            return DEFAULT_INTERFACES_CONFIG.copy()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Fallback if config is corrupted
            return DEFAULT_INTERFACES_CONFIG.copy()

    def _save_config(self, config: Dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def save(self) -> None:
        self._save_config(self.config)

    def get_current_interface(self) -> str:
        return self.config.get("current", "openai")

    def set_current_interface(self, interface: str) -> None:
        if interface in self.config.get("interfaces", {}):
            self.config["current"] = interface
            self.save()
        else:
            raise ValueError(f"Interface '{interface}' not found.")

    def get_interface_config(self, interface: str) -> Dict[str, Any]:
        return self.config.get("interfaces", {}).get(interface, {})

    def update_interface_config(self, interface: str, key: str, value: Any) -> None:
        if interface not in self.config.get("interfaces", {}):
            self.config.setdefault("interfaces", {})[interface] = {}
        
        self.config["interfaces"][interface][key] = value
        self.save()

# Global instance
config_manager = ConfigManager()
