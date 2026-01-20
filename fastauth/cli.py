"""
FastAuth CLI.

Provides command-line utilities for FastAuth projects.

Install with: pip install sreekarnv-fastauth[cli]
"""

import secrets
import sys
from importlib.util import find_spec
from pathlib import Path

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:  # pragma: no cover
    print("CLI requires typer and rich.")
    print("Install with: pip install sreekarnv-fastauth[cli]")
    sys.exit(1)

from fastauth import __version__
from fastauth._compat import HAS_FASTAPI, HAS_HTTPX

app = typer.Typer(
    name="fastauth",
    help="FastAuth CLI - Authentication toolkit for FastAPI",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version():
    """Show FastAuth version."""
    console.print(f"[bold blue]fastauth[/bold blue] {__version__}")


@app.command()
def check():
    """Check installation and dependencies."""
    console.print(
        Panel.fit(
            f"[bold blue]FastAuth[/bold blue] v{__version__}",
            subtitle="Dependency Check",
        )
    )

    core_table = Table(
        title="Core Dependencies", show_header=True, header_style="bold cyan"
    )
    core_table.add_column("Package", style="white")
    core_table.add_column("Status", justify="center")

    core_deps = [
        ("argon2-cffi", "argon2"),
        ("python-jose", "jose"),
        ("pydantic-settings", "pydantic_settings"),
        ("email-validator", "email_validator"),
        ("itsdangerous", "itsdangerous"),
        ("sqlmodel", "sqlmodel"),
    ]

    for name, module in core_deps:
        installed = find_spec(module) is not None
        status = "[green]OK[/green]" if installed else "[red]MISSING[/red]"
        core_table.add_row(name, status)

    console.print(core_table)
    console.print()

    peer_table = Table(
        title="Peer Dependencies", show_header=True, header_style="bold cyan"
    )
    peer_table.add_column("Package", style="white")
    peer_table.add_column("Status", justify="center")
    peer_table.add_column("Note", style="dim")

    hint = "" if HAS_FASTAPI else "pip install fastapi"
    status = "[green]OK[/green]" if HAS_FASTAPI else "[red]MISSING[/red]"
    peer_table.add_row("fastapi", status, hint)

    console.print(peer_table)
    console.print()

    opt_table = Table(
        title="Optional Dependencies", show_header=True, header_style="bold cyan"
    )
    opt_table.add_column("Package", style="white")
    opt_table.add_column("Extra", style="dim")
    opt_table.add_column("Status", justify="center")
    opt_table.add_column("Note", style="dim")

    hint = "" if HAS_HTTPX else "pip install sreekarnv-fastauth[oauth]"
    status = "[green]OK[/green]" if HAS_HTTPX else "[yellow]--[/yellow]"
    opt_table.add_row("httpx", "[oauth]", status, hint)

    has_typer = find_spec("typer") is not None
    status = "[green]OK[/green]" if has_typer else "[yellow]--[/yellow]"
    opt_table.add_row("typer", "[cli]", status, "")

    has_rich = find_spec("rich") is not None
    status = "[green]OK[/green]" if has_rich else "[yellow]--[/yellow]"
    opt_table.add_row("rich", "[cli]", status, "")

    console.print(opt_table)
    console.print()

    if HAS_FASTAPI:
        console.print("[bold green]Ready to use![/bold green]")
    else:
        console.print("[bold red]FastAPI required![/bold red]")
        console.print("Install with: [cyan]pip install fastapi[/cyan]")
        raise typer.Exit(1)


@app.command("generate-secret")
def generate_secret(
    length: int = typer.Option(64, "--length", "-l", help="Length of the secret key"),
    env_format: bool = typer.Option(False, "--env", "-e", help="Output in .env format"),
):
    """Generate a secure secret key for JWT tokens."""
    secret = secrets.token_hex(length // 2)

    if env_format:
        console.print(f"[cyan]SECRET_KEY[/cyan]={secret}")
    else:
        console.print(f"[green]{secret}[/green]")


@app.command()
def init(
    directory: Path = typer.Argument(Path("."), help="Directory to initialize"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
):
    """Initialize a new FastAuth project with boilerplate files."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    files_created = []

    env_example = directory / ".env.example"
    if not env_example.exists() or force:
        env_example.write_text(
            f"""SECRET_KEY={secrets.token_hex(32)}
DATABASE_URL=sqlite:///./app.db
EMAIL_BACKEND=console
REQUIRE_EMAIL_VERIFICATION=false
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
"""
        )
        files_created.append(".env.example")

    app_dir = directory / "app"
    app_dir.mkdir(exist_ok=True)

    init_file = app_dir / "__init__.py"
    if not init_file.exists() or force:
        init_file.write_text("")
        files_created.append("app/__init__.py")

    db_file = app_dir / "database.py"
    if not db_file.exists() or force:
        db_file.write_text(
            '''"""Database configuration."""

from sqlmodel import Session, SQLModel, create_engine

from app.settings import settings

engine = create_engine(settings.database_url, echo=False)


def init_db():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
'''
        )
        files_created.append("app/database.py")

    settings_file = app_dir / "settings.py"
    if not settings_file.exists() or force:
        settings_file.write_text(
            '''"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    database_url: str = "sqlite:///./app.db"
    secret_key: str = "change-me-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
    )


settings = Settings()
'''
        )
        files_created.append("app/settings.py")

    main_file = app_dir / "main.py"
    if not main_file.exists() or force:
        main_file.write_text(
            '''"""FastAPI application with FastAuth."""

from fastapi import FastAPI

from fastauth import auth_router, account_router, sessions_router
from fastauth.api import dependencies

from app.database import get_session, init_db

app = FastAPI(title="FastAuth App")


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    init_db()


app.include_router(auth_router)
app.include_router(account_router)
app.include_router(sessions_router)

app.dependency_overrides[dependencies.get_session] = get_session


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "FastAuth App", "docs": "/docs"}
'''
        )
        files_created.append("app/main.py")

    if files_created:
        console.print("[bold green]Project initialized![/bold green]\n")

        table = Table(title="Created Files", show_header=True, header_style="bold cyan")
        table.add_column("File", style="white")
        table.add_column("Status", justify="center")

        for f in files_created:
            table.add_row(f, "[green]OK[/green]")

        console.print(table)
        console.print()
        console.print("Next steps:")
        console.print("  1. [cyan]cp .env.example .env[/cyan]")
        console.print("  2. [cyan]uvicorn app.main:app --reload[/cyan]")
        console.print("  3. Open http://localhost:8000/docs")
    else:
        console.print("[yellow]No files created (already exist).[/yellow]")
        console.print("[yellow]Use --force to overwrite.[/yellow]")


@app.command()
def providers():
    """List available OAuth providers."""
    table = Table(title="OAuth Providers", show_header=True, header_style="bold cyan")
    table.add_column("Provider", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Note", style="dim")

    if HAS_HTTPX:
        status = "[green]OK[/green]"
        note = ""
    else:
        status = "[yellow]--[/yellow]"
        note = "requires [oauth]"
    table.add_row("Google", status, note)

    table.add_row("GitHub", "[blue]coming soon[/blue]", "")
    table.add_row("Microsoft", "[blue]coming soon[/blue]", "")
    table.add_row("Apple", "[blue]coming soon[/blue]", "")
    table.add_row("Discord", "[blue]coming soon[/blue]", "")

    console.print(table)

    if not HAS_HTTPX:
        console.print()
        console.print(
            "Install OAuth: [cyan]pip install sreekarnv-fastauth[oauth][/cyan]"
        )


if __name__ == "__main__":  # pragma: no cover
    app()
