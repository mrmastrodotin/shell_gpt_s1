"""
CLI command for executing approved agent commands
"""

import click
import subprocess
import sys
from pathlib import Path


@click.command()
@click.argument('command_or_exec_id')
@click.option('--session', '-s', help='Session ID (for exec_id lookup)')
def run(command_or_exec_id, session):
    """
    Execute an approved agent command
    
    Usage:
        sgpt run <exec_id>
        sgpt run "command string"
    """
    from sgpt.agent.execution import ExecutionTracker
    
    # Determine storage path
    storage_path = Path.home() / ".sgpt" / "agent_sessions"
    tracker = ExecutionTracker(storage_path)
    
    # Check if it's an exec_id
    if command_or_exec_id.startswith("exec_"):
        exec_id = command_or_exec_id
        status_data = tracker.get_status(exec_id)
        
        if not status_data:
            click.echo(f"❌ Execution {exec_id} not found")
            sys.exit(1)
        
        command = status_data["command"]
        click.echo(f"📋 Executing: {command}")
    else:
        command = command_or_exec_id
        exec_id = None
    
    # Mark as running if we have exec_id
    if exec_id:
        tracker.mark_running(exec_id)
    
    # Execute command
    click.echo(f"\n🚀 Running command...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        exit_code = result.returncode
        output = result.stdout
        error = result.stderr
        
        # Display output
        if output:
            click.echo("\n📤 Output:")
            click.echo(output)
        
        if error:
            click.echo("\n⚠️  Errors:")
            click.echo(error)
        
        click.echo(f"\n✅ Exit code: {exit_code}")
        
        # Save result if we have exec_id
        if exec_id:
            tracker.save_result(exec_id, exit_code, output, error)
            click.echo(f"💾 Result saved to execution {exec_id}")
        
        sys.exit(exit_code)
        
    except subprocess.TimeoutExpired:
        click.echo("\n⏱️  Command timed out (5 minutes)")
        if exec_id:
            tracker.save_result(exec_id, -1, "", "Timeout after 5 minutes")
        sys.exit(1)
        
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        if exec_id:
            tracker.save_result(exec_id, -1, "", str(e))
        sys.exit(1)
