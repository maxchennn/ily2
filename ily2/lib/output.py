from rich.console import Console
from rich.panel import Panel

console = Console()


def banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]ILY2[/bold cyan] — guided Gentoo Linux installer\n"
            "[dim]inspired by archinstall[/dim]",
            border_style="cyan",
        )
    )


def step(title: str) -> None:
    console.rule(f"[bold green]{title}")


def info(msg: str) -> None:
    console.print(f"[cyan]•[/cyan] {msg}")


def success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def warn(msg: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {msg}")


def error(msg: str) -> None:
    console.print(f"[bold red]✗ {msg}[/bold red]")
