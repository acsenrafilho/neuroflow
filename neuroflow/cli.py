"""Rich CLI entry point for NeuroFlow."""

import argparse
from shutil import which

from rich.console import Console
from rich.table import Table

from neuroflow import __version__
from neuroflow.config import get_settings
from neuroflow.tools.registry import list_tools

console = Console()


def main() -> None:
    """Print version and environment status."""
    parser = argparse.ArgumentParser(prog="neuroflow", description="NeuroFlow CLI")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print package version and exit",
    )
    args = parser.parse_args()

    if args.version:
        console.print(__version__)
        return

    settings = get_settings()
    table = Table(title="NeuroFlow")
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    table.add_row("Version", __version__)
    table.add_row("Environment", settings.neuroflow_env)
    table.add_row("Data root", str(settings.data_root))
    table.add_row(
        "Data root exists",
        "[green]yes[/green]" if settings.data_root.is_dir() else "[yellow]no[/yellow]",
    )
    console.print(table)

    tools_table = Table(title="Registered tools")
    tools_table.add_column("ID")
    tools_table.add_column("Available")
    tools_table.add_column("Page")
    for tool in list_tools():
        available = tool.is_available()
        if tool.executable:
            path = which(tool.executable) or "not found"
            status = f"[green]{path}[/green]" if available else f"[red]{path}[/red]"
        else:
            status = "[dim]coming soon[/dim]"
        tools_table.add_row(tool.id, status, tool.page_path)
    console.print(tools_table)
