import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from fastauth.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for version command."""

    def test_version_output(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "fastauth" in result.output


class TestCheckCommand:
    """Tests for check command."""

    def test_check_shows_dependencies(self):
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "Core Dependencies" in result.output
        assert "Peer Dependencies" in result.output
        assert "Optional Dependencies" in result.output

    def test_check_shows_fastapi_status(self):
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "fastapi" in result.output

    def test_check_ready_message(self):
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0
        assert "Ready to use" in result.output

    def test_check_fails_when_fastapi_missing(self):
        with patch("fastauth.cli.HAS_FASTAPI", False):
            result = runner.invoke(app, ["check"])
            assert result.exit_code == 1
            assert "FastAPI required" in result.output


class TestGenerateSecretCommand:
    """Tests for generate-secret command."""

    def test_generate_secret_default_length(self):
        result = runner.invoke(app, ["generate-secret"])
        assert result.exit_code == 0
        secret = result.output.strip()
        assert len(secret) == 64

    def test_generate_secret_custom_length(self):
        result = runner.invoke(app, ["generate-secret", "--length", "32"])
        assert result.exit_code == 0
        secret = result.output.strip()
        assert len(secret) == 32

    def test_generate_secret_env_format(self):
        result = runner.invoke(app, ["generate-secret", "--env"])
        assert result.exit_code == 0
        assert "SECRET_KEY=" in result.output


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, ["init", tmpdir])
            assert result.exit_code == 0
            assert "Project initialized" in result.output

            assert (Path(tmpdir) / ".env.example").exists()
            assert (Path(tmpdir) / "app" / "__init__.py").exists()
            assert (Path(tmpdir) / "app" / "database.py").exists()
            assert (Path(tmpdir) / "app" / "settings.py").exists()
            assert (Path(tmpdir) / "app" / "main.py").exists()

    def test_init_skips_existing_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", tmpdir])
            result = runner.invoke(app, ["init", tmpdir])
            assert result.exit_code == 0
            assert "No files created" in result.output

    def test_init_force_overwrites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runner.invoke(app, ["init", tmpdir])
            result = runner.invoke(app, ["init", tmpdir, "--force"])
            assert result.exit_code == 0
            assert "Project initialized" in result.output


class TestProvidersCommand:
    """Tests for providers command."""

    def test_providers_shows_google(self):
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "Google" in result.output

    def test_providers_shows_coming_soon(self):
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "coming soon" in result.output
        assert "GitHub" in result.output
        assert "Microsoft" in result.output

    def test_providers_shows_install_hint_when_httpx_missing(self):
        with patch("fastauth.cli.HAS_HTTPX", False):
            result = runner.invoke(app, ["providers"])
            assert result.exit_code == 0
            assert "Install OAuth" in result.output


class TestHelpCommand:
    """Tests for help output."""

    def test_help_shows_all_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "version" in result.output
        assert "check" in result.output
        assert "generate-secret" in result.output
        assert "init" in result.output
        assert "providers" in result.output
