"""Rich CLI entry point for NeuroFlow."""

import argparse

from rich.console import Console
from rich.table import Table

from neuroflow import __version__
from neuroflow.config import get_settings

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
    table.add_row("BIDS root", str(settings.bids_root))
    table.add_row(
        "BIDS root exists",
        "[green]yes[/green]" if settings.bids_root.is_dir() else "[yellow]no[/yellow]",
    )
    console.print(table)
    if not settings.bids_root.is_dir():
        console.print(
            "[dim]Run scripts/fetch_sample_bids.sh to download a public sample dataset.[/dim]"
        )


if __name__ == "__main__":
    main()
