import re

import pytest

typer_testing = pytest.importorskip("typer.testing")
CliRunner = typer_testing.CliRunner

from fastauth import __version__  # noqa: E402
from fastauth.cli import app  # noqa: E402

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in _strip_ansi(result.output)


def test_generate_secret_default_length():
    result = runner.invoke(app, ["generate-secret"])
    assert result.exit_code == 0
    secret = result.output.strip()
    assert len(secret) > 20


def test_generate_secret_custom_length():
    result = runner.invoke(app, ["generate-secret", "--length", "32"])
    assert result.exit_code == 0
    assert len(result.output.strip()) > 0


def test_check_runs():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "fastapi" in result.output.lower()


def test_providers_runs():
    result = runner.invoke(app, ["providers"])
    assert result.exit_code == 0
    assert "credentials" in result.output.lower()
    assert "google" in result.output.lower()
    assert "github" in result.output.lower()


def test_init_creates_files(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "main.py").exists()
    assert (tmp_path / "fastauth_config.py").exists()
    assert "Next steps" in result.output


def test_init_skips_existing_files(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "Skipped" in result.output


def test_init_force_overwrites(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(app, ["init", "--force", str(tmp_path)])
    assert result.exit_code == 0
    assert "Created" in result.output


def test_init_default_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (tmp_path / "main.py").exists()


def test_init_scaffolded_files_contain_expected_content(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    config_content = (tmp_path / "fastauth_config.py").read_text()
    main_content = (tmp_path / "main.py").read_text()
    assert "FastAuthConfig" in config_content
    assert "FastAPI" in main_content
