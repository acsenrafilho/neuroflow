"""Rich CLI entry point for NeuroFlow."""

import argparse

from rich.console import Console
from rich.table import Table

from neuroflow import __version__
from neuroflow.config import Settings, get_settings
from neuroflow.tools.host_probe import module_available, scan_all_packages
from neuroflow.tools.registry import list_modules, list_tools

console = Console()


def _print_environment(settings: Settings) -> None:
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


def _print_status(settings: Settings) -> None:
    _print_environment(settings)
    results = scan_all_packages(settings)

    tools_table = Table(title="Registered packages")
    tools_table.add_column("ID")
    tools_table.add_column("Ready")
    tools_table.add_column("Resolved path")
    tools_table.add_column("Detail")
    for tool in list_tools():
        probe = results[tool.id]
        ready = "[green]yes[/green]" if probe.available else "[red]no[/red]"
        path = probe.resolved_path or "—"
        tools_table.add_row(tool.id, ready, path, probe.detail)
    console.print(tools_table)


def _print_scan(settings: Settings) -> None:
    results = scan_all_packages(settings)

    packages_table = Table(title="Host package scan")
    packages_table.add_column("Package")
    packages_table.add_column("Ready")
    packages_table.add_column("Resolved path")
    packages_table.add_column("Detail")
    for tool in list_tools():
        probe = results[tool.id]
        ready = "[green]yes[/green]" if probe.available else "[red]no[/red]"
        packages_table.add_row(
            tool.name,
            ready,
            probe.resolved_path or "—",
            probe.detail,
        )
    console.print(packages_table)

    modules_table = Table(title="Processing modules")
    modules_table.add_column("Package")
    modules_table.add_column("Module")
    modules_table.add_column("Portal")
    modules_table.add_column("Host ready")
    for module in list_modules():
        host_ready = module_available(results, module, settings)
        portal = "coming soon" if module.coming_soon else "active"
        ready = "[green]yes[/green]" if host_ready else "[red]no[/red]"
        modules_table.add_row(module.package_name, module.module_name, portal, ready)
    console.print(modules_table)


def main() -> None:
    """Print version and environment status."""
    parser = argparse.ArgumentParser(prog="neuroflow", description="NeuroFlow CLI")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print package version and exit",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("scan", help="Scan localhost for installed neuroimaging packages")

    args = parser.parse_args()

    if args.version:
        console.print(__version__)
        return

    settings = get_settings()
    if args.command == "scan":
        _print_scan(settings)
        return

    _print_status(settings)

