"""
CLI Formatter
Rich formatting utilities for beautiful CLI output
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.tree import Tree
from typing import List, Dict, Any
import time

# Global console instance
console = Console()


class AgentFormatter:
    """Format agent output with rich styling"""
    
    @staticmethod
    def print_header(title: str, subtitle: str = None):
        """Print styled header"""
        panel_content = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            panel_content += f"\n[dim]{subtitle}[/dim]"
        
        console.print(Panel(panel_content, border_style="cyan", padding=(1, 2)))
    
    @staticmethod
    def print_phase(phase: str, description: str = None):
        """Print phase transition"""
        content = f"[bold yellow]📍 Phase: {phase.upper()}[/bold yellow]"
        if description:
            content += f"\n[dim]{description}[/dim]"
        
        console.print(Panel(content, border_style="yellow", padding=(0, 2)))
    
    @staticmethod
    def print_command(command: str, tool: str = None):
        """Print proposed command"""
        content = f"[bold green]🔧 Proposed Command[/bold green]\n\n"
        
        if tool:
            content += f"[dim]Tool: {tool}[/dim]\n"
        
        # Syntax highlight the command
        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
        
        console.print(Panel(content, border_style="green"))
        console.print(syntax)
    
    @staticmethod
    def print_approval_prompt(command: str) -> bool:
        """Print approval prompt and get user response"""
        console.print("\n[bold yellow]⚠️  Human Approval Required[/bold yellow]")
        console.print(f"   Command: [cyan]{command}[/cyan]")
        
        response = console.input("\n   [bold]Approve command? (y/N):[/bold] ")
        return response.lower() in ['y', 'yes']
    
    @staticmethod
    def print_execution(exec_id: str, command: str):
        """Print execution instructions"""
        panel = Panel(
            f"[bold cyan]Execution ID:[/bold cyan] {exec_id}\n\n"
            f"[bold]To execute, run:[/bold]\n"
            f"[green]sgpt run {exec_id}[/green]\n\n"
            f"[dim]Or use the full command:[/dim]\n"
            f"[dim]{command}[/dim]",
            border_style="cyan",
            title="[bold]⏳ Awaiting Execution[/bold]",
            padding=(1, 2)
        )
        console.print(panel)
    
    @staticmethod
    def print_result(exit_code: int, output: str = None, error: str = None):
        """Print execution result"""
        if exit_code == 0:
            status = "[bold green]✅ SUCCESS[/bold green]"
            border_color = "green"
        else:
            status = f"[bold red]❌ FAILED (exit code: {exit_code})[/bold red]"
            border_color = "red"
        
        content = status
        
        if output:
            content += f"\n\n[bold]Output:[/bold]\n{output[:500]}"
            if len(output) > 500:
                content += "\n[dim]... (truncated)[/dim]"
        
        if error:
            content += f"\n\n[bold red]Error:[/bold red]\n{error[:500]}"
        
        console.print(Panel(content, border_style=border_color, padding=(1, 2)))
    
    @staticmethod
    def print_facts(facts: Dict[str, Any]):
        """Print discovered facts"""
        table = Table(title="📊 Discovered Facts", border_style="cyan")
        
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Count", style="green", justify="right")
        table.add_column("Items", style="white")
        
        if facts.get('live_hosts'):
            table.add_row(
                "Live Hosts",
                str(len(facts['live_hosts'])),
                ", ".join(facts['live_hosts'][:5]) + ("..." if len(facts['live_hosts']) > 5 else "")
            )
        
        if facts.get('open_ports'):
            table.add_row(
                "Open Ports",
                str(len(facts['open_ports'])),
                ", ".join([f"{p['ip']}:{p['port']}" for p in facts['open_ports'][:5]])
            )
        
        if facts.get('vulnerabilities'):
            table.add_row(
                "Vulnerabilities",
                str(len(facts['vulnerabilities'])),
                f"{sum(1 for v in facts['vulnerabilities'] if v.get('severity') == 'critical')} critical"
            )
        
        if facts.get('targets'):
            table.add_row(
                "Targets",
                str(len(facts['targets'])),
                ", ".join(facts['targets'][:5])
            )
        
        console.print(table)
    
    @staticmethod
    def print_tools(tools: Dict[str, bool]):
        """Print tool availability"""
        table = Table(title="🛠️  Tool Availability", border_style="cyan")
        
        table.add_column("Tool", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Category", style="dim")
        
        # Categorize tools
        categories = {
            'nmap': 'Discovery',
            'gobuster': 'Web',
            'nikto': 'Web',
            'curl': 'Web',
            'enum4linux': 'Enumeration',
            'hydra': 'Exploitation',
            'whatweb': 'Web',
            'python_script': 'Scripting'
        }
        
        for tool, available in sorted(tools.items()):
            status = "[green]✓ Installed[/green]" if available else "[red]✗ Missing[/red]"
            category = categories.get(tool, 'Other')
            table.add_row(tool, status, category)
        
        console.print(table)
    
    @staticmethod
    def print_session_summary(session: Dict[str, Any]):
        """Print session summary"""
        tree = Tree(f"[bold cyan]📋 Session: {session.get('session_id', 'Unknown')}[/bold cyan]")
        
        # Goal
        tree.add(f"[bold]Goal:[/bold] {session.get('goal', 'N/A')}")
        
        # Phase
        tree.add(f"[bold]Phase:[/bold] {session.get('phase', 'N/A')}")
        
        # Stats
        stats = tree.add("[bold]Statistics[/bold]")
        stats.add(f"Commands: {len(session.get('commands_executed', []))}")
        stats.add(f"Hosts Found: {len(session.get('facts', {}).get('live_hosts', []))}")
        stats.add(f"Vulnerabilities: {len(session.get('facts', {}).get('vulnerabilities', []))}")
        
        # Status
        if session.get('done'):
            tree.add("[green]✅ Goal Satisfied[/green]")
        else:
            tree.add("[yellow]⏳ In Progress[/yellow]")
        
        console.print(tree)
    
    @staticmethod
    def create_progress() -> Progress:
        """Create a progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        )
    
    @staticmethod
    def print_error(message: str, details: str = None):
        """Print error message"""
        content = f"[bold red]❌ Error[/bold red]\n\n{message}"
        
        if details:
            content += f"\n\n[dim]{details}[/dim]"
        
        console.print(Panel(content, border_style="red", padding=(1, 2)))
    
    @staticmethod
    def print_success(message: str):
        """Print success message"""
        console.print(f"[bold green]✅ {message}[/bold green]")
    
    @staticmethod
    def print_warning(message: str):
        """Print warning message"""
        console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
    
    @staticmethod
    def print_info(message: str):
        """Print info message"""
        console.print(f"[cyan]ℹ️  {message}[/cyan]")


# Convenience functions
def header(title: str, subtitle: str = None):
    """Print header"""
    AgentFormatter.print_header(title, subtitle)

def phase(phase: str, description: str = None):
    """Print phase"""
    AgentFormatter.print_phase(phase, description)

def command(cmd: str, tool: str = None):
    """Print command"""
    AgentFormatter.print_command(cmd, tool)

def approval_prompt(cmd: str) -> bool:
    """Get approval"""
    return AgentFormatter.print_approval_prompt(cmd)

def success(message: str):
    """Print success"""
    AgentFormatter.print_success(message)

def error(message: str, details: str = None):
    """Print error"""
    AgentFormatter.print_error(message, details)

def warning(message: str):
    """Print warning"""
    AgentFormatter.print_warning(message)

def info(message: str):
    """Print info"""
    AgentFormatter.print_info(message)
