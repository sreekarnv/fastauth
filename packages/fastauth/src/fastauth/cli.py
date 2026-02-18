from __future__ import annotations

import secrets
import sys
from pathlib import Path

try:
    import typer
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print(
        "CLI dependencies not installed. Run: pip install sreekarnv-fastauth[cli]",
        file=sys.stderr,
    )
    sys.exit(1)

from fastauth import __version__
from fastauth._compat import (
    HAS_AIOSMTPLIB,
    HAS_ARGON2,
    HAS_FASTAPI,
    HAS_HTTPX,
    HAS_JOSERFC,
    HAS_REDIS,
    HAS_SQLALCHEMY,
    _has_package,
)

app = typer.Typer(
    name="fastauth",
    help="FastAuth CLI - NextAuth inspired authentication for FastAPI.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    console.print(f"FastAuth v{__version__}")


@app.command()
def generate_secret(
    length: int = typer.Option(64, "--length", "-l", help="Byte length of the token."),
) -> None:
    console.print(secrets.token_urlsafe(length))


_EXTRAS: list[tuple[str, str, bool]] = [
    ("fastapi", "fastapi", HAS_FASTAPI),
    ("jwt", "joserfc", HAS_JOSERFC),
    ("jwt", "cryptography", _has_package("cryptography")),
    ("oauth", "httpx", HAS_HTTPX),
    ("sqlalchemy", "sqlalchemy", HAS_SQLALCHEMY),
    ("sqlalchemy", "aiosqlite", _has_package("aiosqlite")),
    ("redis", "redis", HAS_REDIS),
    ("argon2", "argon2-cffi", HAS_ARGON2),
    ("email", "aiosmtplib", HAS_AIOSMTPLIB),
    ("email", "jinja2", _has_package("jinja2")),
    ("cli", "typer", True),
    ("cli", "rich", True),
]


@app.command()
def check() -> None:
    table = Table(
        title=f"FastAuth v{__version__} — Dependency Status",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Extra", style="cyan")
    table.add_column("Package", style="white")
    table.add_column("Status")

    for extra, pkg, installed in _EXTRAS:
        if installed:
            status = "[green]✓  installed[/green]"
        else:
            status = (
                f"[red]✗  missing[/red]   "
                f"[dim]pip install sreekarnv-fastauth[{extra}][/dim]"
            )
        table.add_row(extra, pkg, status)

    console.print(table)


_PROVIDERS: list[tuple[str, str, str | None]] = [
    ("credentials", "Built-in email/password provider.", None),
    ("google", "Google OAuth 2.0 (OIDC).", "oauth"),
    ("github", "GitHub OAuth 2.0.", "oauth"),
]


@app.command()
def providers() -> None:
    table = Table(
        title="FastAuth - Available Providers",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Provider", style="cyan")
    table.add_column("Description")
    table.add_column("Requires extra")
    table.add_column("Status")

    for name, description, extra in _PROVIDERS:
        if extra is None:
            status = "[green]✓  ready[/green]"
            req = "[dim]—[/dim]"
        elif _has_package("httpx"):
            status = "[green]✓  ready[/green]"
            req = f"[dim]{extra}[/dim]"
        else:
            status = (
                f"[red]✗  missing[/red]   "
                f"[dim]pip install sreekarnv-fastauth[{extra}][/dim]"
            )
            req = f"[dim]{extra}[/dim]"

        table.add_row(name, description, req, status)

    console.print(table)


_CONFIG_TEMPLATE = """\
from fastauth import FastAuth, FastAuthConfig
from fastauth.providers.credentials import CredentialsProvider
from fastauth.adapters.sqlalchemy import SQLAlchemyAdapter

# Replace with the output of: fastauth generate-secret
SECRET = "change-me-in-production"

adapter = SQLAlchemyAdapter(engine_url="sqlite+aiosqlite:///./auth.db")

config = FastAuthConfig(
    secret=SECRET,
    providers=[CredentialsProvider()],
    adapter=adapter.user,
    token_adapter=adapter.token,
    base_url="http://localhost:8000",
)

auth = FastAuth(config)
"""

_MAIN_TEMPLATE = """\
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastauth_config import adapter, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await adapter.create_tables()
    yield


app = FastAPI(lifespan=lifespan)
auth.mount(app)
"""


@app.command()
def init(
    output_dir: Path = typer.Argument(  # noqa: B008
        Path("."),
        help="Directory to scaffold the project into.",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing files."
    ),
) -> None:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "fastauth_config.py": _CONFIG_TEMPLATE,
        "main.py": _MAIN_TEMPLATE,
    }

    created: list[str] = []
    skipped: list[str] = []

    for filename, content in files.items():
        target = output_dir / filename
        if target.exists() and not force:
            skipped.append(filename)
        else:
            target.write_text(content, encoding="utf-8")
            created.append(filename)

    for f in created:
        console.print(f"[green]Created  [bold]{f}[/bold][/green]")
    for f in skipped:
        console.print(
            f"[yellow]Skipped  [bold]{f}[/bold][/yellow]"
            f"[dim](already exists - use --force to overwrite)[/dim]"
        )

    if created:
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("  1. Replace SECRET in [cyan]fastauth_config.py[/cyan] with:")
        console.print("       [dim]fastauth generate-secret[/dim]")
        console.print("  2. Run your app:")
        console.print("       [dim]uvicorn main:app --reload[/dim]")
