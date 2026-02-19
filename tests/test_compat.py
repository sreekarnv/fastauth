import pytest
from fastauth._compat import HAS_FASTAPI, HAS_SQLALCHEMY, _has_package, require
from fastauth.exceptions import MissingDependencyError


def test_has_package_existing():
    assert _has_package("sys") is True


def test_has_package_missing():
    assert _has_package("nonexistent_package_xyz_abc_123") is False


def test_require_existing_does_not_raise():
    require("sys", "test")


def test_require_missing_raises():
    with pytest.raises(MissingDependencyError):
        require("nonexistent_package_xyz_abc_123", "myextra")


def test_missing_dependency_error_message():
    with pytest.raises(MissingDependencyError) as exc:
        require("some_missing_pkg", "myextra")
    assert "some_missing_pkg" in str(exc.value)
    assert "myextra" in str(exc.value)


def test_has_fastapi_flag():
    assert HAS_FASTAPI is True


def test_has_sqlalchemy_flag():
    assert HAS_SQLALCHEMY is True
