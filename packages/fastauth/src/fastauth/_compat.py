import importlib


def _has_package(package_name: str) -> bool:
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def require(package_name: str, extra: str) -> None:
    if not _has_package(package_name):
        from fastauth.exceptions import MissingDependencyError

        raise MissingDependencyError(package_name, extra)


HAS_FASTAPI = _has_package("fastapi")
HAS_JOSERFC = _has_package("joserfc")
HAS_HTTPX = _has_package("httpx")
HAS_SQLALCHEMY = _has_package("sqlalchemy")
HAS_REDIS = _has_package("redis")
HAS_ARGON2 = _has_package("argon2")
HAS_AIOSMTPLIB = _has_package("aiosmtplib")
