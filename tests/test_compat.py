"""Tests for the _compat module."""

from unittest.mock import patch

import pytest

from fastauth._compat import (
    HAS_FASTAPI,
    HAS_HTTPX,
    MissingDependencyError,
    require_fastapi,
    require_httpx,
)


class TestDependencyFlags:
    """Tests for dependency detection flags."""

    def test_has_fastapi_is_true_when_installed(self):
        assert HAS_FASTAPI is True

    def test_has_httpx_is_true_when_installed(self):
        assert HAS_HTTPX is True


class TestMissingDependencyError:
    """Tests for MissingDependencyError exception."""

    def test_error_message_format(self):
        error = MissingDependencyError("testpkg", "Install with: pip install testpkg")
        assert "'testpkg' is required" in str(error)
        assert "Install with: pip install testpkg" in str(error)

    def test_error_attributes(self):
        error = MissingDependencyError("mypkg", "Install hint here")
        assert error.package == "mypkg"
        assert error.install_hint == "Install hint here"

    def test_is_import_error_subclass(self):
        error = MissingDependencyError("pkg", "hint")
        assert isinstance(error, ImportError)


class TestRequireFastapi:
    """Tests for require_fastapi function."""

    def test_does_not_raise_when_fastapi_installed(self):
        require_fastapi()

    def test_raises_when_fastapi_not_installed(self):
        with patch("fastauth._compat.HAS_FASTAPI", False):
            with pytest.raises(MissingDependencyError) as exc_info:
                require_fastapi()
            assert exc_info.value.package == "fastapi"
            assert "pip install fastapi" in exc_info.value.install_hint


class TestRequireHttpx:
    """Tests for require_httpx function."""

    def test_does_not_raise_when_httpx_installed(self):
        require_httpx()

    def test_raises_when_httpx_not_installed(self):
        with patch("fastauth._compat.HAS_HTTPX", False):
            with pytest.raises(MissingDependencyError) as exc_info:
                require_httpx()
            assert exc_info.value.package == "httpx"
            assert "fastauth[oauth]" in exc_info.value.install_hint
