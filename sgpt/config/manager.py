"""
Configuration Manager
Load and manage ShellGPT configuration from YAML files and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class LLMConfig:
    """LLM configuration"""
    interface: str = "openai"  # openai, gemini, ollama, web
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    retry_attempts: int = 3
    retry_delay: float = 2.0


@dataclass
class ExecutionConfig:
    """Execution configuration"""
    timeout: int = 300  # 5 minutes
    max_pending: int = 10
    auto_cleanup: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    enable_rotation: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 7


@dataclass
class SafetyConfig:
    """Safety configuration"""
    require_approval: bool = True
    enable_validation: bool = True
    allowed_networks: list = None
    blocked_commands: list = None
    
    def __post_init__(self):
        if self.allowed_networks is None:
            self.allowed_networks = []
        if self.blocked_commands is None:
            self.blocked_commands = []


@dataclass
class StorageConfig:
    """Storage configuration"""
    sessions_dir: Optional[Path] = None
    logs_dir: Optional[Path] = None
    reports_dir: Optional[Path] = None
    
    def __post_init__(self):
        # Set defaults
        base_dir = Path.home() / ".sgpt"
        if self.sessions_dir is None:
            self.sessions_dir = base_dir / "agent_sessions"
        if self.logs_dir is None:
            self.logs_dir = base_dir / "logs"
        if self.reports_dir is None:
            self.reports_dir = base_dir / "reports"
        
        # Ensure paths are Path objects
        self.sessions_dir = Path(self.sessions_dir)
        self.logs_dir = Path(self.logs_dir)
        self.reports_dir = Path(self.reports_dir)


@dataclass
class AgentConfig:
    """Complete agent configuration"""
    llm: LLMConfig
    execution: ExecutionConfig
    logging: LoggingConfig
    safety: SafetyConfig
    storage: StorageConfig


class ConfigManager:
    """Manage ShellGPT configuration"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.config: Optional[AgentConfig] = None
        self._config_path = Path.home() / ".sgpt" / "config.yaml"
        self._initialized = True
    
    def load(self, config_path: Path = None) -> AgentConfig:
        """
        Load configuration from file and environment
        
        Priority (highest to lowest):
        1. Environment variables
        2. User config file (~/.sgpt/config.yaml)
        3. Default values
        
        Args:
            config_path: Optional custom config path
            
        Returns:
            AgentConfig instance
        """
        if config_path:
            self._config_path = Path(config_path)
        
        # Start with defaults
        config_dict = self._get_defaults()
        
        # Load from file if exists
        if self._config_path.exists():
            with open(self._config_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}
                config_dict = self._merge_configs(config_dict, file_config)
        
        # Override with environment variables
        env_config = self._load_from_env()
        config_dict = self._merge_configs(config_dict, env_config)
        
        # Create config objects
        self.config = AgentConfig(
            llm=LLMConfig(**config_dict.get('llm', {})),
            execution=ExecutionConfig(**config_dict.get('execution', {})),
            logging=LoggingConfig(**config_dict.get('logging', {})),
            safety=SafetyConfig(**config_dict.get('safety', {})),
            storage=StorageConfig(**config_dict.get('storage', {}))
        )
        
        return self.config
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'llm': asdict(LLMConfig()),
            'execution': asdict(ExecutionConfig()),
            'logging': asdict(LoggingConfig()),
            'safety': asdict(SafetyConfig()),
            'storage': asdict(StorageConfig())
        }
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {
            'llm': {},
            'execution': {},
            'logging': {},
            'safety': {},
            'storage': {}
        }
        
        # LLM settings
        if os.getenv('SGPT_LLM_INTERFACE'):
            env_config['llm']['interface'] = os.getenv('SGPT_LLM_INTERFACE')
        if os.getenv('SGPT_LLM_MODEL'):
            env_config['llm']['model'] = os.getenv('SGPT_LLM_MODEL')
        if os.getenv('SGPT_LLM_TEMPERATURE'):
            env_config['llm']['temperature'] = float(os.getenv('SGPT_LLM_TEMPERATURE'))
        if os.getenv('SGPT_LLM_MAX_TOKENS'):
            env_config['llm']['max_tokens'] = int(os.getenv('SGPT_LLM_MAX_TOKENS'))
        
        # Execution settings
        if os.getenv('SGPT_EXEC_TIMEOUT'):
            env_config['execution']['timeout'] = int(os.getenv('SGPT_EXEC_TIMEOUT'))
        
        # Logging settings
        if os.getenv('SGPT_LOG_LEVEL'):
            env_config['logging']['console_level'] = os.getenv('SGPT_LOG_LEVEL')
        
        # Safety settings
        if os.getenv('SGPT_REQUIRE_APPROVAL'):
            env_config['safety']['require_approval'] = os.getenv('SGPT_REQUIRE_APPROVAL').lower() == 'true'
        
        # Storage settings
        if os.getenv('SGPT_STORAGE_DIR'):
            base = Path(os.getenv('SGPT_STORAGE_DIR'))
            env_config['storage']['sessions_dir'] = str(base / "agent_sessions")
            env_config['storage']['logs_dir'] = str(base / "logs")
            env_config['storage']['reports_dir'] = str(base / "reports")
        
        return env_config
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save(self, config_path: Path = None):
        """Save current configuration to file"""
        if config_path:
            self._config_path = Path(config_path)
        
        # Ensure directory exists
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict
        config_dict = {
            'llm': asdict(self.config.llm),
            'execution': asdict(self.config.execution),
            'logging': asdict(self.config.logging),
            'safety': asdict(self.config.safety),
            'storage': {
                'sessions_dir': str(self.config.storage.sessions_dir),
                'logs_dir': str(self.config.storage.logs_dir),
                'reports_dir': str(self.config.storage.reports_dir)
            }
        }
        
        # Write YAML
        with open(self._config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def get(self) -> AgentConfig:
        """Get current configuration (load if not loaded)"""
        if self.config is None:
            self.load()
        return self.config
    
    def create_default_config(self):
        """Create default config file"""
        self.config = AgentConfig(
            llm=LLMConfig(),
            execution=ExecutionConfig(),
            logging=LoggingConfig(),
            safety=SafetyConfig(),
            storage=StorageConfig()
        )
        self.save()


# Global instance
_config_manager = None

def get_config() -> AgentConfig:
    """Get global configuration"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get()
