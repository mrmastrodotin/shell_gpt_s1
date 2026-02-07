"""
Agent Logger
Structured logging system for ShellGPT agent
"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any


class AgentLogger:
    """Centralized logging system for agent operations"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize logger (only once)"""
        if self._initialized:
            return
        
        self.logger = logging.getLogger("sgpt")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        self._initialized = True
    
    def setup(
        self,
        log_dir: Path = None,
        console_level: str = "INFO",
        file_level: str = "DEBUG",
        enable_rotation: bool = True
    ):
        """
        Setup logging configuration
        
        Args:
            log_dir: Directory for log files
            console_level: Console logging level (DEBUG, INFO, WARNING, ERROR)
            file_level: File logging level
            enable_rotation: Enable log rotation
        """
        # Default log directory
        if log_dir is None:
            log_dir = Path.home() / ".sgpt" / "logs"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, console_level.upper()))
        console_handler.setFormatter(ConsoleFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        if enable_rotation:
            # Rotate daily, keep 7 days
            file_handler = TimedRotatingFileHandler(
                log_dir / "sgpt.log",
                when="midnight",
                interval=1,
                backupCount=7
            )
        else:
            # Simple rotating file handler
            file_handler = RotatingFileHandler(
                log_dir / "sgpt.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
        
        file_handler.setLevel(getattr(logging, file_level.upper()))
        file_handler.setFormatter(FileFormatter())
        self.logger.addHandler(file_handler)
        
        # JSON log for structured data
        json_handler = RotatingFileHandler(
            log_dir / "sgpt_structured.json",
            maxBytes=10 * 1024 * 1024,
            backupCount=3
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=True, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, exc_info=True, extra=kwargs)
    
    # Specialized logging methods
    
    def log_agent_step(self, phase: str, step: str, details: Dict[str, Any] = None):
        """Log agent step (THINK, PLAN, PROPOSE, etc.)"""
        self.info(
            f"Agent Step: {phase} -> {step}",
            phase=phase,
            step=step,
            details=details or {}
        )
    
    def log_llm_call(self, prompt_type: str, tokens: int = None, model: str = None):
        """Log LLM API call"""
        self.info(
            f"LLM Call: {prompt_type}",
            prompt_type=prompt_type,
            tokens=tokens,
            model=model
        )
    
    def log_tool_execution(self, tool: str, command: str, exit_code: int):
        """Log tool execution"""
        self.info(
            f"Tool Execution: {tool}",
            tool=tool,
            command=command,
            exit_code=exit_code
        )
    
    def log_fact_update(self, fact_type: str, count: int):
        """Log fact database update"""
        self.debug(
            f"Fact Update: {fact_type}",
            fact_type=fact_type,
            count=count
        )
    
    def log_phase_transition(self, from_phase: str, to_phase: str, reason: str):
        """Log phase transition"""
        self.info(
            f"Phase Transition: {from_phase} -> {to_phase}",
            from_phase=from_phase,
            to_phase=to_phase,
            reason=reason
        )


class ConsoleFormatter(logging.Formatter):
    """Colorful console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format: [TIME] LEVEL: message
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        return f"{color}[{timestamp}] {record.levelname:8s}{reset}: {record.getMessage()}"


class FileFormatter(logging.Formatter):
    """Detailed file formatter"""
    
    def format(self, record):
        """Format log record for file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Include extra fields if present
        extra = ""
        if hasattr(record, 'phase'):
            extra += f" [phase={record.phase}]"
        if hasattr(record, 'tool'):
            extra += f" [tool={record.tool}]"
        
        return f"{timestamp} {record.levelname:8s} {record.name}: {record.getMessage()}{extra}"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields
        if hasattr(record, 'phase'):
            log_data['phase'] = record.phase
        if hasattr(record, 'step'):
            log_data['step'] = record.step
        if hasattr(record, 'tool'):
            log_data['tool'] = record.tool
        if hasattr(record, 'command'):
            log_data['command'] = record.command
        if hasattr(record, 'exit_code'):
            log_data['exit_code'] = record.exit_code
        if hasattr(record, 'details'):
            log_data['details'] = record.details
        
        return json.dumps(log_data)


# Global logger instance
_logger = None

def get_logger() -> AgentLogger:
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = AgentLogger()
    return _logger
