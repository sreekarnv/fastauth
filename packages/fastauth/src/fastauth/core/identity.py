from __future__ import annotations


def normalize_email(email: str) -> str:
    """Return FastAuth's canonical email identity form."""
    return email.strip().casefold()
