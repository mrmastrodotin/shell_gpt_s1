"""
Config module
"""

from sgpt.config.manager import ConfigManager, get_config, AgentConfig
from sgpt.config.legacy import (
    SHELL_GPT_CONFIG_FOLDER,
    SHELL_GPT_CONFIG_PATH,
    ROLE_STORAGE_PATH,
    FUNCTIONS_PATH,
    CHAT_CACHE_PATH,
    CACHE_PATH,
    DEFAULT_CONFIG,
    Config,
    cfg,
)

__all__ = [
    'ConfigManager', 
    'get_config', 
    'AgentConfig', 
    'cfg',
    'SHELL_GPT_CONFIG_FOLDER',
    'SHELL_GPT_CONFIG_PATH',
    'ROLE_STORAGE_PATH',
    'FUNCTIONS_PATH',
    'CHAT_CACHE_PATH',
    'CACHE_PATH',
    'DEFAULT_CONFIG',
    'Config',
]
