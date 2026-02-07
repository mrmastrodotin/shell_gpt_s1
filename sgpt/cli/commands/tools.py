"""
CLI command for checking tool availability
"""

import click
from sgpt.tools.registry import ToolRegistry
from sgpt.tools.availability import ToolAvailabilityChecker


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed version info')
def tools(verbose):
    """Check which red-team tools are available"""
    
    registry = ToolRegistry()
    registry.load_tools()
    
    # Generate and print report
    report = ToolAvailabilityChecker.generate_report(registry)
    print(report)
    
    # Get unavailable tools
    availability = ToolAvailabilityChecker.check_all(registry)
    unavailable = [binary for binary, available in availability.items() if not available]
    
    if unavailable:
        print("\n💡 Installation Suggestions:")
        suggestions = ToolAvailabilityChecker.install_suggestions(unavailable)
        for tool, suggestion in suggestions.items():
            print(f"   {tool}: {suggestion}")
