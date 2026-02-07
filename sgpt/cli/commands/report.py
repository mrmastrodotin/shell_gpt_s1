"""
CLI command for generating session reports
"""

import click
from pathlib import Path
import sys


@click.command()
@click.argument('session_id')
@click.option('--output', '-o', help='Output file path', default=None)
def report(session_id, output):
    """Generate markdown report for agent session"""
    
    from sgpt.agent.persistence import AgentPersistence
    from sgpt.reporting.generator import ReportGenerator
    
    # Load session
    storage_path = Path.home() / ".sgpt" / "agent_sessions"
    persistence = AgentPersistence(storage_path)
    
    try:
        state = persistence.load_state(session_id)
    except FileNotFoundError:
        click.echo(f"❌ Session {session_id} not found")
        sys.exit(1)
    
    # Generate report
    click.echo(f"📊 Generating report for session: {session_id}")
    
    # Determine output path
    if output:
        output_path = Path(output)
    else:
        output_path = storage_path / session_id / f"{session_id}_report.md"
    
    report_content = ReportGenerator.generate(state, output_path)
    
    click.echo(f"\n✅ Report generated: {output_path}")
    click.echo(f"   Session: {state.goal}")
    click.echo(f"   Hosts: {len(state.facts.live_hosts)}")
    click.echo(f"   Targets: {len(state.facts.targets)}")
    click.echo(f"   Commands: {len(state.commands_executed)}")
    
    # Show preview
    if not output:
        click.echo(f"\n📄 Preview:")
        click.echo("─" * 60)
        lines = report_content.split('\n')
        for line in lines[:20]:  # First 20 lines
            click.echo(line)
        click.echo("...")
        click.echo("─" * 60)
