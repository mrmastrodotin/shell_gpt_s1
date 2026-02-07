"""
Agent CLI Commands
sgpt agent start/resume/status/stop
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
import asyncio
import uuid

from sgpt.agent import Agent, AgentState
from sgpt.agent.persistence import AgentPersistence
from sgpt.tools import ToolRegistry
from sgpt.config import SHELL_GPT_CONFIG_FOLDER
from sgpt.context.builder import build_context

agent_app = typer.Typer(help="Agent automation commands")
console = Console()


@agent_app.command("start")
def agent_start(
    goal: str = typer.Option(..., "--goal", "-g", help="Agent goal/objective"),
    session_id: str = typer.Option(None, "--session", "-s", help="Custom session ID"),
    interface: str = typer.Option(None, "--interface", "-i", help="LLM interface (openai, gemini, ollama, web)"),
    model: str = typer.Option(None, "--model", "-m", help="Model name")
):
    """Start new agent session"""
    
    # Generate or use provided session ID
    if not session_id:
        session_id = f"agent_{uuid.uuid4().hex[:8]}"
    
    console.print(f"\n🚀 Starting agent session: [cyan]{session_id}[/cyan]")
    console.print(f"🎯 Goal: {goal}\n")
    
    # Build auto-context
    console.print("🔍 Building context...")
    auto_context = build_context()
    context_dict = {
        "system": {
            "os": auto_context.system.os,
            "distro": auto_context.system.distro,
            "user": auto_context.system.user,
            "shell": auto_context.system.shell
        },
        "network": {
            "ip": auto_context.network.ip,
            "subnet": auto_context.network.subnet
        },
        "tools": auto_context.tools
    }
    
    # Initialize agent state
    state = AgentState.initialize(
        session_id=session_id,
        goal=goal,
        auto_context=context_dict
    )
    state.tools_available = auto_context.tools
    
    # Create persistence
    persistence = AgentPersistence(SHELL_GPT_CONFIG_FOLDER)
    persistence.save_state(state)
    
    # Initialize tool registry
    tool_registry = ToolRegistry()
    tool_registry.load_tools()
    
    console.print(f"✅ Context built")
    console.print(f"✅ {len(tool_registry.list_all())} tools loaded\n")
    
    # Initialize LLM adapter
    from sgpt.agent.llm_adapter import AgentLLMAdapter
    llm = AgentLLMAdapter(interface=interface, model=model)
    
    console.print(f"🤖 LLM: {llm.interface}/{llm.model}\n")
    
    # Create and run agent
    agent = Agent(
        state=state,
        persistence=persistence,
        tool_registry=tool_registry,
        llm_provider=llm
    )
    
    # Run async loop
    asyncio.run(agent.run())


@agent_app.command("resume")
def agent_resume(
    session_id: str = typer.Argument(..., help="Session ID to resume")
):
    """Resume paused agent session"""
    
    persistence = AgentPersistence(SHELL_GPT_CONFIG_FOLDER)
    
    if not persistence.session_exists(session_id):
        console.print(f"[red]❌ Session not found: {session_id}[/red]")
        raise typer.Exit(1)
    
    state = persistence.load_state(session_id)
    
    if state.done:
        console.print(f"[yellow]⚠️  Session already completed[/yellow]")
        raise typer.Exit(0)
    
    console.print(f"\n▶️  Resuming session: [cyan]{session_id}[/cyan]")
    console.print(f"🎯 Goal: {state.goal}")
    console.print(f"📍 Phase: {state.phase.value}\n")
    
    # Initialize tool registry
    tool_registry = ToolRegistry()
    tool_registry.load_tools()
    
    # Initialize LLM (use stored config or default)
    from sgpt.agent.llm_adapter import AgentLLMAdapter
    llm = AgentLLMAdapter()
    
    # Create and run agent
    agent = Agent(
        state=state,
        persistence=persistence,
        tool_registry=tool_registry,
        llm_provider=llm
    )
    
    asyncio.run(agent.run())


@agent_app.command("status")
def agent_status(
    session_id: str = typer.Argument(None, help="Session ID (optional, shows all if not provided)")
):
    """Show agent session status"""
    
    persistence = AgentPersistence(SHELL_GPT_CONFIG_FOLDER)
    
    if session_id:
        # Show specific session
        if not persistence.session_exists(session_id):
            console.print(f"[red]❌ Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        
        state = persistence.load_state(session_id)
        
        console.print(f"\n📊 Session: [cyan]{session_id}[/cyan]")
        console.print(f"🎯 Goal: {state.goal}")
        console.print(f"📍 Phase: {state.phase.value}")
        console.print(f"✅ Completed: {state.done}")
        console.print(f"\n📈 Stats:")
        console.print(f"   Commands: {len(state.commands_executed)}")
        console.print(f"   Failures: {len(state.failures)}")
        console.print(f"   Hosts: {len(state.facts.live_hosts)}")
        console.print(f"   Targets: {len(state.facts.targets)}")
        console.print(f"   LLM calls: {state.llm_calls}")
        
        if state.waiting_for_approval:
            console.print(f"\n⏳ Waiting for approval:")
            console.print(f"   {state.proposed_command}")
    
    else:
        # List all sessions
        sessions = persistence.list_sessions()
        
        if not sessions:
            console.print("\n📭 No agent sessions found")
            return
        
        table = Table(title="Agent Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Goal")
        table.add_column("Phase", style="yellow")
        table.add_column("Status")
        table.add_column("Steps")
        
        for sid in sessions:
            state = persistence.load_state(sid)
            status = "✅ Done" if state.done else ("⏳ Waiting" if state.waiting_for_approval else "▶️ Running")
            table.add_row(
                sid,
                state.goal[:40] + "..." if len(state.goal) > 40 else state.goal,
                state.phase.value,
                status,
                str(len(state.commands_executed))
            )
        
        console.print(table)


@agent_app.command("stop")
def agent_stop(
    session_id: str = typer.Argument(..., help="Session ID to stop")
):
    """Stop running agent session"""
    
    persistence = AgentPersistence(SHELL_GPT_CONFIG_FOLDER)
    
    if not persistence.session_exists(session_id):
        console.print(f"[red]❌ Session not found: {session_id}[/red]")
        raise typer.Exit(1)
    
    state = persistence.load_state(session_id)
    state.done = True
    state.waiting_for_approval = False
    persistence.save_state(state)
    
    console.print(f"🛑 Session stopped: {session_id}")
