
from typing import Optional
import os

# To allow users to use arrow keys in the REPL.
import readline  # noqa: F401
import sys
import subprocess

import typer
from click import BadArgumentUsage
from click.types import Choice
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import confirm

from sgpt.config import cfg
from sgpt.config_manager import config_manager
from sgpt.function import get_openai_schemas
from sgpt.handlers.chat_handler import ChatHandler
from sgpt.gemini_tools.gemini import fetch_gemini_models, get_gemini_api_key
from sgpt.openai_tools.utils import list_openai_models
from sgpt.credentials import save_credentials, get_credentials, set_api_key
from sgpt.web.browser import BrowserSession
from sgpt.web.utils import check_consent
# Patching client after config loading
import sgpt.handlers.handler as handler_module
from sgpt.handlers.default_handler import DefaultHandler
from sgpt.handlers.repl_handler import ReplHandler
from sgpt.llm_functions.init_functions import install_functions as inst_funcs
from sgpt.role import DefaultRoles, SystemRole
from sgpt.utils import (
    get_edited_prompt,
    get_sgpt_version,
    install_shell_integration,
    option_callback,
    run_command,
)
from sgpt.context.builder import build_context as build_auto_context
from sgpt.context.session import get_session_file_path, get_context_file_path, save_session, load_session, add_command_record
from sgpt.context.renderer import render_context
from sgpt.context.resolver import resolve_behavior
from sgpt.context.models import BehaviorRules
import json
import dataclasses


app = typer.Typer(
    rich_markup_mode="markdown", 
    help="ShellGPT - Your intelligent shell assistant.", 
    add_completion=False
)

@option_callback
def configure_interface(cls, value: bool):
    if not value:
        return
    
    current = config_manager.get_current_interface()
    current_display = current
    # UX Improvement: Cleaner prompt wording
    typer.echo("Available interfaces:")
    typer.echo(f"[1] OpenAI API {'(current)' if current == 'openai' else ''}")
    typer.echo(f"[2] Ollama (local / remote) {'(current)' if current == 'ollama' else ''}")
    typer.echo("[3] Gemini API (Google)")
    typer.echo("[4] Web Automation (Experimental)")
    
    choice = typer.prompt(f"Select interface [1-4] (current: {current_display})", default=1)
    
    if choice == 1:
        config_manager.set_current_interface("openai")
        typer.echo("Switched to OpenAI API.")
    elif choice == 2:
        config_manager.set_current_interface("ollama")
        typer.echo("Switched to Ollama.")
    elif choice == 3:
        config_manager.set_current_interface("gemini")
        typer.echo("Switched to Gemini API.")
    elif choice == 4:
        config_manager.set_current_interface("web-automation")
        typer.echo("Switched to Web Automation (Experimental).")
    else:
        typer.echo("Invalid choice.")
    
    raise typer.Exit()

@option_callback
def set_interface(cls, value: str):
    if not value:
        return
    
    interface = value.lower()
    try:
        config_manager.set_current_interface(interface)
        typer.echo(f"Switched to {interface}.")
    except ValueError:
        typer.echo(f"Error: Interface '{interface}' not found. Available: openai, ollama, gemini, web-automation.")
    
    raise typer.Exit()

@option_callback
def show_status(cls, value: bool):
    if not value:
        return
    
    current = config_manager.get_current_interface()
    # Helper to get display name
    display_name = "OpenAI API"
    if current == "ollama": display_name = "Ollama"
    elif current == "web-automation": display_name = "Web Automation (Experimental)"
    elif current == "gemini": display_name = "Gemini API"
    
    typer.echo(f"Current interface: {display_name}")
    
    if current == "web-automation":
        web_config = config_manager.get_interface_config("web-automation")
        provider = web_config.get("provider", "chatgpt")
        typer.echo(f"Web provider: {provider}")
        
    elif current == "ollama":
        ollama_config = config_manager.get_interface_config("ollama")
        host = ollama_config.get("host", "http://localhost:11434")
        model = ollama_config.get("model", "llama3")
        typer.echo("Ollama:")
        typer.echo(f"  host: {host}")
        typer.echo(f"  model: {model}")
    
    elif current == "gemini":
        gemini_config = config_manager.get_interface_config("gemini")
        model = gemini_config.get("model", "gemini-1.5-flash")
        typer.echo("Gemini API:")
        typer.echo(f"  model: {model}")
        
    raise typer.Exit()

@option_callback
def configure_ollama_host(cls, value: bool):
    if not value:
        return
    # Check if value is a flag usage or actually a value. 
    # Since we defined likely as an option taking a string, it might be the host itself.
    # But for "interactive configuration", the user might just pass the flag. 
    # Actually, let's make it interactive if no value, but typer option needs a value or flag.
    # Better: use a boolean flag to trigger interactive mode? Or just accept value.
    # The requirement says "interactive commands".
    # Let's support both: if passed `--ollama-host URL` set it.
    # But wait, we want interactive selection.
    # Let's make it simple: this callback is for updating the config.
    
    # Actually, the user requirement: `sgpt --ollama-host` -> interactive menu.
    # So this should be is_flag=True? But typer doesn't let us easily do both flag and value.
    # Let's stick to interactive menu if called.
    # Wait, the user example showed `sgpt --ollama-host` with NO arguments for interactive.
    # So it should be is_flag=True.
    
    config = config_manager.get_interface_config("ollama")
    current_host = config.get("host", "http://localhost:11434")
    
    typer.echo("Known Ollama hosts:")
    typer.echo(f"[1] http://localhost:11434 {'(current)' if current_host == 'http://localhost:11434' else ''}")
    typer.echo("[2] Add new host")
    
    choice = typer.prompt("Select host", type=str, default="1")
    
    if choice == "1":
        new_host = "http://localhost:11434"
    elif choice == "2":
        new_host = typer.prompt("Enter new Ollama host URL")
    else:
        # If they typed a URL directly or something else
        # Just assume it might be a valid selection if we had a list, 
        # but here we simplify.
        if choice.startswith("http"):
             new_host = choice
        else:
             typer.echo("Invalid choice.")
             raise typer.Exit()

    config_manager.update_interface_config("ollama", "host", new_host)
    typer.echo(f"Ollama host set to: {new_host}")
    raise typer.Exit()

@option_callback
def configure_ollama_model(cls, value: bool):
    if not value:
        return
    
    config = config_manager.get_interface_config("ollama")
    current_model = config.get("model", "llama3")
    host = config.get("host", "http://localhost:11434")
    
    typer.echo(f"Current Ollama model: {current_model}")
    # Optional: fetch models from host
    try:
        import requests
        typer.echo(f"Fetching models from {host}...")
        response = requests.get(f"{host}/api/tags", timeout=2)
        if response.status_code == 200:
            models = [m["name"] for m in response.json().get("models", [])]
            if models:
                typer.echo("Available models:")
                for i, m in enumerate(models, 1):
                    typer.echo(f"[{i}] {m}")
                
                choice = typer.prompt("Select model", type=str, default="1")
                if choice.isdigit() and 1 <= int(choice) <= len(models):
                     new_model = models[int(choice) - 1]
                else:
                     new_model = choice
            else:
                 typer.echo("No models found on host.")
                 new_model = typer.prompt("Enter model name", default=current_model)
        else:
            typer.echo("Failed to fetch models.")
            new_model = typer.prompt("Enter model name", default=current_model)
            
    except Exception as e:
        typer.echo(f"Could not connect to Ollama host: {e}")
        new_model = typer.prompt("Enter model name", default=current_model)

    config_manager.update_interface_config("ollama", "model", new_model)
    typer.echo(f"Ollama model set to: {new_model}")
    raise typer.Exit()

@option_callback
def configure_web_model(cls, value: bool):
    if not value:
        return
    
    web_config = config_manager.get_interface_config("web-automation")
    # Define available providers
    providers = {
            "chatgpt": "https://chatgpt.com",
            "gemini": "https://gemini.google.com",
            "claude": "https://claude.ai"
    }
    current_default = web_config.get("provider", "chatgpt")
    
    typer.echo(f"Current Web Automation provider: {current_default}")
    typer.echo("Available Web Providers:")
    provider_names = list(providers.keys())
    for i, name in enumerate(provider_names, 1):
        typer.echo(f"[{i}] {name}")
    
    choice = typer.prompt("Select default provider", type=str, default="1")
    
    new_default = None
    if choice.isdigit() and 1 <= int(choice) <= len(provider_names):
        new_default = provider_names[int(choice) - 1]
    elif choice in providers:
        new_default = choice
    else:
        typer.echo("Invalid choice.")
        raise typer.Exit()
        
    config_manager.update_interface_config("web-automation", "provider", new_default)
    typer.echo(f"Web Automation provider set to: {new_default}")
    raise typer.Exit()

@option_callback
def configure_api_key(cls, value: bool):
    if not value:
        return
    
    typer.echo("Select API to configure:")
    typer.echo("[1] OpenAI")
    typer.echo("[2] Gemini")
    typer.echo("[3] Cancel")
    
    choice = typer.prompt("Select option", type=int, default=3)
    
    if choice == 1:
        provider = "openai"
        display_name = "OpenAI"
    elif choice == 2:
        provider = "gemini"
        display_name = "Gemini"
    else:
        raise typer.Exit()
        
    api_key = typer.prompt(f"Enter {display_name} API key", hide_input=True)
    
    if api_key:
        set_api_key(provider, api_key)
        typer.echo(f"{display_name} API key saved securely.")
        
    raise typer.Exit()

@option_callback
def show_api_keys(cls, value: bool):
    if not value:
        return
    
    from sgpt.credentials import get_api_key
    from sgpt.gemini_tools.gemini import get_gemini_api_key
    
    typer.echo("API Key Status:")
    typer.echo("")
    
    # Check OpenAI
    openai_key = cfg.get("OPENAI_API_KEY") or get_api_key("openai")
    if openai_key:
        typer.secho("✓ OpenAI API Key: Found", fg="green")
        # Validate
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            client.models.list(timeout=5.0)
            typer.secho("  Status: Valid", fg="green")
        except Exception as e:
            typer.secho(f"  Status: Invalid ({str(e)[:50]}...)", fg="red")
    else:
        typer.secho("✗ OpenAI API Key: Not Found", fg="red")
    
    typer.echo("")
    
    # Check Gemini
    gemini_key = get_gemini_api_key()
    if gemini_key:
        typer.secho("✓ Gemini API Key: Found", fg="green")
        # Validate
        try:
            from sgpt.gemini_tools.gemini import fetch_gemini_models
            fetch_gemini_models(gemini_key)
            typer.secho("  Status: Valid", fg="green")
        except Exception as e:
            typer.secho(f"  Status: Invalid ({str(e)[:50]}...)", fg="red")
    else:
        typer.secho("✗ Gemini API Key: Not Found", fg="red")
    
    raise typer.Exit()

@option_callback
def clear_api_keys(cls, value: bool):
    if not value:
        return
    
    from sgpt.credentials import delete_api_key
    
    typer.echo("Select API key to clear:")
    typer.echo("[1] OpenAI")
    typer.echo("[2] Gemini")
    typer.echo("[3] All")
    typer.echo("[4] Cancel")
    
    choice = typer.prompt("Select option", type=int, default=4)
    
    if choice == 1:
        # Clear OpenAI only
        if delete_api_key("openai"):
            typer.secho("✓ OpenAI API Key: Cleared", fg="yellow")
        else:
            typer.echo("  OpenAI API Key: Not found")
    elif choice == 2:
        # Clear Gemini only
        if delete_api_key("gemini"):
            typer.secho("✓ Gemini API Key: Cleared", fg="yellow")
        else:
            typer.echo("  Gemini API Key: Not found")
    elif choice == 3:
        # Clear All
        typer.echo("")
        openai_cleared = delete_api_key("openai")
        gemini_cleared = delete_api_key("gemini")
        
        if openai_cleared:
            typer.secho("✓ OpenAI API Key: Cleared", fg="yellow")
        else:
            typer.echo("  OpenAI API Key: Not found")
            
        if gemini_cleared:
            typer.secho("✓ Gemini API Key: Cleared", fg="yellow")
        else:
            typer.echo("  Gemini API Key: Not found")
        
        if openai_cleared or gemini_cleared:
            typer.echo("")
            typer.secho("All API keys cleared from secure storage.", fg="green")
    else:
        # Cancel
        typer.echo("Cancelled.")
    
    raise typer.Exit()




@option_callback
def configure_gemini_model(cls, value: str):
    if not value:
        return
    
    # Non-interactive mode: if value is not a flag (assumed if it's not the boolean default True/False which Typer usually handles, but here we defined it as bool in previous step? Wait.)
    # In previous step `gemini_model` was `bool`.
    # To support `sgpt --gemini-model gemini-1.5-pro`, I need to change the type hint in `main` to `str` (optional) or `value` usage here.
    # But `value` here comes from the callback.
    # User requested: `sgpt --gemini-model gemini-1.5-flash`
    # This means `gemini_model` option in `main` MUST be `str`, not `bool`.
    # I will fix `main` signature in the next tool call.
    # Here I assume `value` is the string passed.
    
    # If the user passed the flag WITHOUT a value (e.g. `sgpt --gemini-model`), Typer might pass the option name or something if implicit? 
    # Actually, for `str` options, you MUST provide a value unless `is_flag=False` (default for str).
    # But we want it to be optional. 
    # If we want `sgpt --gemini-model` (no arg) to trigger interactive, it's tricky with Typer's `Option`.
    # Typer/Click standard: `Option(..., "--flag", is_flag=False)` expects a value.
    # To support BOTH, we usually use `is_flag=False` and make it optional? 
    # Or `is_flag=True` but that prevents passing a string.
    # The user example `sgpt --gemini-model gemini-1.5-flash` implies it accepts a value.
    # The user example `sgpt --gemini-model` (interactive) implies it might NOT accept a value?
    # User said: "Non-interactive override ... If provided: set directly... no prompt".
    # This implies the interactive mode is the default when NO value is provided? 
    # But strict CLI argument parsing usually requires a value for string options.
    # Let's assume WE ONLY SUPPORT `sgpt --gemini-model MODEL_NAME` for non-interactive.
    # For interactive, maybe just `sgpt --gemini-model`? 
    # BUT if I change type to `str`, `sgpt --gemini-model` will fail saying "Argument required".
    # WORKAROUND: Use `kwarg_name` or similar? No.
    # Maybe use a specific value for interactive? e.g. `sgpt --gemini-model list`?
    # OR, rely on the fact that `configure_interface` allows selecting Gemini, maybe put model selection THERE?
    # NO, user specifically asked for `sgpt --gemini-model`.
    
    # STRATEGY:
    # Set `gemini_model` to `str`. Make it `Optional` with default `None`.
    # Pass `callback` that handles it.
    # BUT if user types `sgpt --gemini-model` without arg, Click complains.
    # Unless we make `flag_value`. 
    # `typer.Option(None, "--gemini-model", flag_value="INTERACTIVE")`
    # If user runs `sgpt --gemini-model`, value is "INTERACTIVE".
    # If user runs `sgpt --gemini-model foo`, value is "foo".
    # This is the way.

    if value == "INTERACTIVE":
        # Interactive Mode
        api_key = get_gemini_api_key()
def configure_gemini_model(cls, value: bool):
    if not value:
        return
    
    api_key = get_gemini_api_key()
    if not api_key:
        typer.echo("Gemini API key not found. Please set GOOGLE_API_KEY environment variable.")
        raise typer.Exit(code=1)

    typer.echo("Fetching available Gemini models...")
    try:
        models = fetch_gemini_models(api_key)
    except Exception as e:
        typer.echo(f"Error fetching models: {e}")
        # Allow custom entry fallback? No, models fetch failed.
        # But maybe user wants Custom?
        if typer.confirm("Fetch failed. Enter model MANUALLY?", default=False):
             models = [] # Custom
        else:
             raise typer.Exit(code=1)

    if not models and not typer.confirm("No models found. Enter model MANUALLY?", default=False):
        typer.echo("No content generation models found.")
        raise typer.Exit(code=1)

    gemini_config = config_manager.get_interface_config("gemini")
    current_model = gemini_config.get("model", "gemini-1.5-flash")
    
    typer.echo("Available Gemini Models:")
    for i, m in enumerate(models, 1):
        name = m.get('name', 'Unknown')
        in_tok = m.get('input_tokens', 'N/A')
        out_tok = m.get('output_tokens', 'N/A')
        is_current = " (current)" if name == current_model else ""
        typer.echo(f"[{i}] {name} [In: {in_tok}, Out: {out_tok}]{is_current}")

    if models:
        typer.echo(f"[{len(models)+1}] Custom / Enter Specific Name")
        choice = typer.prompt("Select model", type=int, default=1)
    else:
        choice = 0 # Force custom

    if models and 1 <= choice <= len(models):
        new_model = models[choice - 1]['name']
        config_manager.update_interface_config("gemini", "model", new_model)
        typer.echo(f"Gemini model set to: {new_model}")
    else:
        # Custom
        manual_val = typer.prompt("Enter model name (e.g. gemini-pro)")
        config_manager.update_interface_config("gemini", "model", manual_val)
        typer.echo(f"Gemini model set to: {manual_val}")
        
    raise typer.Exit()

@option_callback
def configure_openai_model(cls, value: bool):
    if not value:
        return
    
    api_key = cfg.get("OPENAI_API_KEY")
    if not api_key:
            typer.echo("OpenAI API key not found.")
            raise typer.Exit(code=1)
    
    typer.echo("Fetching available OpenAI models...")
    try:
        models = list_openai_models(api_key)
    except Exception as e:
        typer.echo(f"Error fetching models: {e}")
        if typer.confirm("Fetch failed. Enter model MANUALLY?", default=False):
             models = []
        else:
             raise typer.Exit(code=1)
        
    if not models and not typer.confirm("No models found. Enter model MANUALLY?", default=False):
            typer.echo("No models found.")
            raise typer.Exit(code=1)
            
    # Default fallback if config not set
    openai_cfg = config_manager.get_interface_config("openai")
    current = openai_cfg.get("model") or cfg.get("DEFAULT_MODEL")
    
    typer.echo("Available OpenAI Models:")
    for i, m in enumerate(models, 1):
        is_current = " (current)" if m == current else ""
        typer.echo(f"[{i}] {m}{is_current}")
        
    if models:
        typer.echo(f"[{len(models)+1}] Custom / Enter Specific Name")
        choice = typer.prompt("Select model", type=int, default=1)
    else:
        choice = 0

    if models and 1 <= choice <= len(models):
            new_model = models[choice-1]
            config_manager.update_interface_config("openai", "model", new_model)
            typer.echo(f"OpenAI model set to: {new_model}")
    else:
         manual_val = typer.prompt("Enter model name (e.g. gpt-4)")
         config_manager.update_interface_config("openai", "model", manual_val)
         typer.echo(f"OpenAI model set to: {manual_val}")
    
    raise typer.Exit()

def apply_runtime_patching(current_interface: str, model: str = None) -> str:
    """Applies runtime environment patching for Ollama/Gemini."""
    import sgpt.handlers.handler as handler_module
    from sgpt.gemini_tools.gemini import get_gemini_api_key
    
    if current_interface == "web":
         config_manager.set_current_interface("web-automation")
         current_interface = "web-automation"

    if current_interface == "openai":
         # Support overriding model via interfaces.json
         openai_config = config_manager.get_interface_config("openai")
         if openai_config and openai_config.get("model"):
             # Only override if model is default (user didn't specify --model)
             if model == cfg.get("DEFAULT_MODEL"):
                 model = openai_config.get("model")

    if current_interface == "ollama":
        ollama_config = config_manager.get_interface_config("ollama")
        host = ollama_config.get("host", "http://localhost:11434")
        ollama_model_name = ollama_config.get("model", "llama3")
        
        os.environ["OPENAI_API_BASE"] = f"{host}/v1"
        os.environ["OPENAI_API_KEY"] = "ollama"
        
        if hasattr(handler_module, "client"):
            handler_module.client.base_url = f"{host}/v1"
            handler_module.client.api_key = "ollama"
        
        if model == cfg.get("DEFAULT_MODEL"):
            model = ollama_model_name

    if current_interface == "gemini":
        gemini_config = config_manager.get_interface_config("gemini")
        base_url = gemini_config.get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/")
        gemini_model_name = gemini_config.get("model", "gemini-1.5-flash")
        
        api_key = get_gemini_api_key()
        if not api_key:
            typer.echo("Error: GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set.")
            raise typer.Exit(code=1)
            
        os.environ["OPENAI_API_BASE"] = base_url
        os.environ["OPENAI_API_KEY"] = api_key
        
        if hasattr(handler_module, "client"):
            handler_module.client.base_url = base_url
            handler_module.client.api_key = api_key
            
        if model == cfg.get("DEFAULT_MODEL") or model == "gpt-3.5-turbo" or model is None:
            model = gemini_model_name
            
    return model

@app.command()
def main(
    prompt: str = typer.Argument(
        "",
        show_default=False,
        help="The prompt to generate completions for.",
    ),
    model: str = typer.Option(
        cfg.get("DEFAULT_MODEL"),
        help="Large language model to use.",
    ),
    temperature: float = typer.Option(
        0.0,
        min=0.0,
        max=2.0,
        help="Randomness of generated output.",
    ),
    top_p: float = typer.Option(
        1.0,
        min=0.0,
        max=1.0,
        help="Limits highest probable tokens (words).",
    ),
    md: bool = typer.Option(
        cfg.get("PRETTIFY_MARKDOWN") == "true",
        help="Prettify markdown output.",
    ),
    shell: bool = typer.Option(
        False,
        "--shell",
        "-s",
        help="Generate and execute shell commands.",
        rich_help_panel="Assistance Options",
    ),
    interaction: bool = typer.Option(
        cfg.get("SHELL_INTERACTION") == "true",
        help="Interactive mode for --shell option.",
        rich_help_panel="Assistance Options",
    ),
    describe_shell: bool = typer.Option(
        False,
        "--describe-shell",
        "-d",
        help="Describe a shell command.",
        rich_help_panel="Assistance Options",
    ),
    code: bool = typer.Option(
        False,
        "--code",
        "-c",
        help="Generate only code.",
        rich_help_panel="Assistance Options",
    ),
    functions: bool = typer.Option(
        cfg.get("OPENAI_USE_FUNCTIONS") == "true",
        help="Allow function calls.",
        rich_help_panel="Assistance Options",
    ),
    editor: bool = typer.Option(
        False,
        help="Open $EDITOR to provide a prompt.",
    ),
    cache: bool = typer.Option(
        True,
        help="Cache completion results.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version.",
        callback=get_sgpt_version,
    ),
    chat: str = typer.Option(
        None,
        help="Follow conversation with id, " 'use "temp" for quick session.',
        rich_help_panel="Chat Options",
    ),
    repl: str = typer.Option(
        None,
        help="Start interactive REPL session with id, " 'use "temp" for quick session.',
        rich_help_panel="Chat Options",
    ),
    show_chat: str = typer.Option(
        None,
        help="Show all messages from provided chat id.",
        rich_help_panel="Chat Options",
    ),
    list_chats: bool = typer.Option(
        False,
        "--list-chats",
        "-lc",
        help="List all existing chat ids.",
        callback=ChatHandler.list_ids,
        rich_help_panel="Chat Options",
    ),
    role: str = typer.Option(
        None,
        help="System role for GPT model.",
        rich_help_panel="Role Options",
    ),
    create_role: str = typer.Option(
        None,
        help="Create role.",
        callback=SystemRole.create,
        rich_help_panel="Role Options",
    ),
    show_role: str = typer.Option(
        None,
        help="Show role.",
        callback=SystemRole.show,
        rich_help_panel="Role Options",
    ),
    list_roles: bool = typer.Option(
        False,
        "--list-roles",
        "-lr",
        help="List roles.",
        callback=SystemRole.list,
        rich_help_panel="Role Options",
    ),
    install_integration: bool = typer.Option(
        False,
        help="Install shell integration (ZSH and Bash only)",
        callback=install_shell_integration,
        hidden=True,  # Hiding since should be used only once.
    ),
    install_functions: bool = typer.Option(
        False,
        help="Install default functions.",
        callback=inst_funcs,
        hidden=True,  # Hiding since should be used only once.
    ),
    # Interactive Configuration Options
    interfaces: bool = typer.Option(
        False,
        "--interfaces",
        help="Interactive Interface Selector.",
        callback=configure_interface,
        rich_help_panel="Interface Options",
    ),
    interface: str = typer.Option(
        None,
        "--interface",
        help="Set current interface (openai/ollama/gemini/web-automation).",
        callback=set_interface,
        rich_help_panel="Interface Options",
    ),
    status: bool = typer.Option(
        False,
        "--status",
        help="Show current interface status.",
        callback=show_status,
        rich_help_panel="Interface Options",
    ),
    ollama_host: bool = typer.Option(
        False,
        "--ollama-host",
        help="Configure Ollama host URL.",
        callback=configure_ollama_host,
        rich_help_panel="Interface Options",
    ),
    ollama_model: bool = typer.Option(
        False,
        "--ollama-model",
        help="Configure Ollama model.",
        callback=configure_ollama_model,
        rich_help_panel="Interface Options",
    ),
    web_model: bool = typer.Option(
        False,
        "--web-model",
        help="Configure default Web provider.",
        callback=configure_web_model,
        rich_help_panel="Interface Options",
    ),
    openai_model: bool = typer.Option(
        False,
        "--openai-model",
        help="Configure OpenAI model.",
        callback=configure_openai_model,
        rich_help_panel="Interface Options",
    ),
    gemini_model: bool = typer.Option(
        False,
        "--gemini-model",
        help="Configure Gemini model.",
        callback=configure_gemini_model,
        rich_help_panel="Interface Options",
    ),
    set_api: bool = typer.Option(
        False,
        "--set-keys",
        help="Interactively configure API keys (OpenAI / Gemini).",
        callback=configure_api_key,
        rich_help_panel="Interface Options",
    ),
    show_keys: bool = typer.Option(
        False,
        "--show-keys",
        help="Show API key validation status.",
        callback=show_api_keys,
        rich_help_panel="Interface Options",
    ),
    clear_keys: bool = typer.Option(
        False,
        "--clear-keys",
        help="Clear all stored API keys.",
        callback=clear_api_keys,
        rich_help_panel="Interface Options",
    ),
    build_context_opt: bool = typer.Option(
        False,
        "--build-context",
        help="Build and enable Auto-Context for this session.",
        rich_help_panel="Context Options",
    ),
    show_context_opt: bool = typer.Option(
        False,
        "--show-context",
        help="Display the current Auto-Context.",
        rich_help_panel="Context Options",
    ),
    clear_context_opt: bool = typer.Option(
        False,
        "--clear-context",
        help="Clear the current Auto-Context cache.",
        rich_help_panel="Context Options",
    ),
) -> None:
    if show_context_opt:
        path = get_context_file_path()
        if not os.path.exists(path):
            typer.echo("Context not found. Run --build-context first.")
        else:
            with open(path, "r") as f:
                typer.echo(f.read())
        raise typer.Exit()

    if clear_context_opt:
        path = get_context_file_path()
        if os.path.exists(path):
            os.remove(path)
            typer.secho("Context cleared.", fg="yellow")
        else:
            typer.echo("No context found.")
        raise typer.Exit()

    if build_context_opt:
        ctx = build_auto_context()
        # Persist context to disk (e.g. static_context.json side-by-side with session)
        session_path = get_session_file_path()
        static_path = session_path.replace("sgpt_session_", "sgpt_context_")
        
        # We need to serialize DataClass to JSON
        with open(static_path, "w") as f:
            json.dump(dataclasses.asdict(ctx), f, default=str, indent=2)
            
        typer.secho("Auto-Context built successfully.", fg="green")
        typer.echo(f"System: {ctx.system.os} {ctx.system.distro}")
        typer.echo(f"User: {ctx.system.user}")
        typer.echo(f"Network: {ctx.network.ip}")
        typer.echo(f"Tools: {len([t for t,v in ctx.tools.items() if v])} detected")
        raise typer.Exit()
    # Phase 2: Runtime Patching based on selected interface
    current_interface = config_manager.get_current_interface()
    model = apply_runtime_patching(current_interface, model)
    
    stdin_passed = not sys.stdin.isatty()

    if stdin_passed:
        stdin = ""
        # TODO: This is very hacky.
        # In some cases, we need to pass stdin along with inputs.
        # When we want part of stdin to be used as a init prompt,
        # but rest of the stdin to be used as a inputs. For example:
        # echo "hello\n__sgpt__eof__\nThis is input" | sgpt --repl temp
        # In this case, "hello" will be used as a init prompt, and
        # "This is input" will be used as "interactive" input to the REPL.
        # This is useful to test REPL with some initial context.
        for line in sys.stdin:
            if "__sgpt__eof__" in line:
                break
            stdin += line
        prompt = f"{stdin}\n\n{prompt}" if prompt else stdin
        try:
            # Switch to stdin for interactive input.
            if os.name == "posix":
                sys.stdin = open("/dev/tty", "r")
            elif os.name == "nt":
                sys.stdin = open("CON", "r")
        except OSError:
            # Non-interactive shell.
            pass

    if show_chat:
        ChatHandler.show_messages(show_chat, md)

    if current_interface == "web-automation":
        if chat:
            typer.echo("Web automation mode: Use --repl for interactive session.")
            raise typer.Exit(code=1)
            
        if not check_consent():
            typer.echo("Consent required to use Web Automation.")
            raise typer.Exit(code=1)
            
        web_config = config_manager.get_interface_config("web-automation")
        provider = web_config.get("provider", "chatgpt")
        
        session = BrowserSession(provider)
        
        try:
            if repl:
                # Interactive Web Session
                session.start()
                typer.secho("Interactive Web Session initiated.", fg="green")
                typer.echo("Type 'exit' or 'quit' to close the session.")
                
                while True:
                    user_input = typer.prompt(">>>", prompt_suffix=" ")
                    if user_input.lower() in ("exit", "quit"):
                        break
                    if not user_input.strip():
                        continue
                        
                    try:
                        result = session.send_prompt(user_input)
                        typer.secho(result, fg="cyan")
                    except Exception as step_error:
                        typer.secho(f"Step Error: {step_error}", fg="red")
                        
            elif prompt:
                # One-off execution
                result = session.run(prompt)
                typer.echo(result)
                
        except Exception as e:
            typer.echo(f"Web Automation Error: {e}")
            raise typer.Exit(code=1)
        finally:
            if repl or prompt:
                 session.close()
        return

    if sum((shell, describe_shell, code)) > 1:
        raise BadArgumentUsage(
            "Only one of --shell, --describe-shell, and --code options can be used at a time."
        )

    if chat and repl:
        raise BadArgumentUsage("--chat and --repl options cannot be used together.")

    if editor and stdin_passed:
        raise BadArgumentUsage("--editor option cannot be used with stdin input.")

    from sgpt.context.models import AutoContext, SystemContext, NetworkContext, RuntimeContext, BehaviorRules
    
    if editor:
        prompt = get_edited_prompt()

    # SECTION: Auto-Context Injection
    # Check if context file exists for this session
    session_path = get_session_file_path()
    static_path = session_path.replace("sgpt_session_", "sgpt_context_")
    
    if os.path.exists(static_path):
        try:
            with open(static_path, "r") as f:
                ctx_data = json.load(f)
            
            # Reconstruct AutoContext
            # Note: We used default=str which makes datetime strings.
            # But SystemContext etc are strings.
            sys_ctx = SystemContext(**ctx_data["system"])
            net_ctx = NetworkContext(**ctx_data["network"])
            tools_ctx = ctx_data["tools"]
            run_ctx = RuntimeContext(**ctx_data["runtime"])
            # Behavior defaults
            beh_ctx = BehaviorRules() 
            
            # Load live session
            sess_ctx = load_session()
            
            # Assemble
            auto_ctx = AutoContext(
                system=sys_ctx,
                network=net_ctx,
                tools=tools_ctx,
                runtime=run_ctx,
                behavior=beh_ctx,
                session=sess_ctx
            )
            
            # Resolve Behavior
            if prompt:
                auto_ctx.behavior = resolve_behavior(prompt, beh_ctx)
                
            # Render
            context_block = render_context(auto_ctx)
            
            # Prepend to prompt (safest injection)
            if prompt:
                prompt = f"{context_block}\n\nUser Request: {prompt}"
            elif repl:
                 # For REPL, we might want to inject it as init prompt
                 # logic below handles init_prompt=prompt
                 prompt = f"{context_block}\n\n(Session Started)"
                 
        except Exception as e:
            # Fallback if corrupted
            # typer.echo(f"Context Error: {e}")
            pass
    # END SECTION

    role_class = (
        DefaultRoles.check_get(shell, describe_shell, code)
        if not role
        else SystemRole.get(role)
    )

    # Disable function calls for Ollama if not supported (optional, but good for stability)
    # For now, we assume Ollama might support usage similarly.
    function_schemas = (get_openai_schemas() or None) if functions else None

    if repl:
        # Will be in infinite loop here until user exits with Ctrl+C.
        ReplHandler(repl, role_class, md).handle(
            init_prompt=prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas,
        )

    if chat:
        full_completion = ChatHandler(chat, role_class, md).handle(
            prompt=prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas,
        )
    else:
        full_completion = DefaultHandler(role_class, md).handle(
            prompt=prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas,
        )

    session: PromptSession[str] = PromptSession()

    while shell and interaction:
        option = typer.prompt(
            text="[E]xecute, [M]odify, [D]escribe, [A]bort",
            type=Choice(("e", "m", "d", "a", "y"), case_sensitive=False),
            default="e" if cfg.get("DEFAULT_EXECUTE_SHELL_CMD") == "true" else "a",
            show_choices=False,
            show_default=False,
        )
        if option in ("e", "y"):
            # "y" option is for keeping compatibility with old version.
            run_command(full_completion)
        elif option == "m":
            full_completion = session.prompt("", default=full_completion)
            continue
        elif option == "d":
            DefaultHandler(DefaultRoles.DESCRIBE_SHELL.get_role(), md).handle(
                full_completion,
                model=model,
                temperature=temperature,
                top_p=top_p,
                caching=cache,
                functions=function_schemas,
            )
            continue
        break


def run_context_wrapper(args: list[str]):
    """
    Handles 'sgpt run <cmd>' specific logic.
    Executes command, captures output, summarizes via LLM, and updates session.
    """
    full_cmd = " ".join(args)
    # typer.echo(f"  [Auto-Context] Executing: {full_cmd}") # Optional debug
    
    # 1. Execute
    try:
        # We use Popen to capture and maybe print? 
        # For simplicity, just run_command (subprocess.run) with capture.
        # But user wants to see output.
        process = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        print(process.stdout, end="")
        print(process.stderr, file=sys.stderr, end="")
        
        combined_out = process.stdout + "\n" + process.stderr
        
        # 2. Summarize (LLM)
        from sgpt.handlers.default_handler import DefaultHandler
        from sgpt.role import SystemRole
        
        summary_system_prompt = "Summarize output in 1-2 factual points. No interpretation. No advice."
        summarizer_role = SystemRole(name="AutoContext", role=summary_system_prompt)
        
        summary_prompt = f"Command: {full_cmd}\nOutput:\n{combined_out[:4000]}" 
        
        # Setup
        current = config_manager.get_current_interface()
        summarizer_interface = current
        
        # Fallback: If Web Automation, use Gemini API for summarization if available
        if current == "web-automation":
            # Check for Gemini Key
            from sgpt.gemini_tools.gemini import get_gemini_api_key
            if get_gemini_api_key():
                summarizer_interface = "gemini"
            # verify ollama?
            # default to openai if no others found (which is default behavior of patcher key)
        
        model = "gpt-3.5-turbo" 
        
        # Apply Patching 
        model = apply_runtime_patching(summarizer_interface, model=model)
            
        # Instantiate handler
        handler = DefaultHandler(summarizer_role, markdown=False)
        messages = handler.make_messages(summary_prompt)
        
        # Call completion directy to capture output (bypass Printer)
        completion_generator = handler.get_completion(
            model=model,
            temperature=0.1,
            top_p=1.0,
            messages=messages,
            functions=None,
            caching=False
        )
        
        summary_text = "".join(completion_generator) 
        
        # 3. Store
        add_command_record(full_cmd, summary_text.strip())
        # typer.secho(f"  [Session] Recorded", fg="magenta") 
        
    except Exception as e:
        typer.secho(f"Error in sgpt run: {e}", fg="red")

def entry_point() -> None:
    # Custom dispatch for 'run' command
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # Shift args: sgpt run echo hello -> sys.argv=["sgpt", "echo", "hello"]
        # We want to pass ["echo", "hello"] to wrapper.
        run_args = sys.argv[2:]
        if not run_args:
             print("Usage: sgpt run <command>")
             sys.exit(1)
        run_context_wrapper(run_args)
    else:
        typer.run(main)


if __name__ == "__main__":
    entry_point()
