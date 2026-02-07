"""
CLI command for configuration management
"""

import click
from pathlib import Path
import sys


@click.group()
def config():
    """Manage ShellGPT configuration"""
    pass


@config.command()
@click.option('--output', '-o', help='Output path for config file', default=None)
def init(output):
    """Initialize default configuration file"""
    from sgpt.config.manager import ConfigManager
    
    manager = ConfigManager()
    
    if output:
        config_path = Path(output)
    else:
        config_path = Path.home() / ".sgpt" / "config.yaml"
    
    if config_path.exists():
        click.echo(f"⚠️  Config file already exists: {config_path}")
        if not click.confirm("Overwrite?"):
            return
    
    manager.create_default_config()
    click.echo(f"✅ Created default config: {config_path}")
    click.echo(f"\n   Edit this file to customize ShellGPT behavior")


@config.command()
def show():
    """Show current configuration"""
    from sgpt.config.manager import get_config
    import yaml
    from dataclasses import asdict
    
    config = get_config()
    
    click.echo("📋 Current Configuration:\n")
    
    config_dict = {
        'llm': asdict(config.llm),
        'execution': asdict(config.execution),
        'logging': asdict(config.logging),
        'safety': asdict(config.safety),
        'storage': {
            'sessions_dir': str(config.storage.sessions_dir),
            'logs_dir': str(config.storage.logs_dir),
            'reports_dir': str(config.storage.reports_dir)
        }
    }
    
    click.echo(yaml.dump(config_dict, default_flow_style=False, indent=2))


@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """Set a configuration value"""
    from sgpt.config.manager import ConfigManager
    
    manager = ConfigManager()
    config = manager.get()
    
    # Parse key path (e.g., "llm.temperature")
    parts = key.split('.')
    
    if len(parts) != 2:
        click.echo("❌ Key must be in format: section.key")
        click.echo("   Example: llm.temperature")
        sys.exit(1)
    
    section, key_name = parts
    
    # Get section
    if not hasattr(config, section):
        click.echo(f"❌ Unknown section: {section}")
        sys.exit(1)
    
    section_obj = getattr(config, section)
    
    # Set value
    if not hasattr(section_obj, key_name):
        click.echo(f"❌ Unknown key: {key_name} in section {section}")
        sys.exit(1)
    
    # Type conversion
    current_value = getattr(section_obj, key_name)
    if isinstance(current_value, bool):
        value = value.lower() == 'true'
    elif isinstance(current_value, int):
        value = int(value)
    elif isinstance(current_value, float):
        value = float(value)
    
    setattr(section_obj, key_name, value)
    
    # Save
    manager.save()
    
    click.echo(f"✅ Set {key} = {value}")
    click.echo(f"   Config saved to: {manager._config_path}")


@config.command()
def validate():
    """Validate configuration file"""
    from sgpt.config.manager import get_config
    
    try:
        config = get_config()
        click.echo("✅ Configuration is valid")
        
        # Check for common issues
        warnings = []
        
        if config.llm.temperature > 1.0:
            warnings.append("⚠️  Temperature > 1.0 may produce unpredictable results")
        
        if not config.safety.require_approval:
            warnings.append("⚠️  Safety approval is disabled - use with caution!")
        
        if warnings:
            click.echo("\nWarnings:")
            for warning in warnings:
                click.echo(f"  {warning}")
        
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}")
        sys.exit(1)
