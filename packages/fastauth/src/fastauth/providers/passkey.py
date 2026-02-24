from __future__ import annotations


class PasskeyProvider:
    """WebAuthn / Passkeys provider."""

    id = "passkey"
    name = "Passkey"
    auth_type = "passkey"

    def __init__(
        self,
        rp_id: str,
        rp_name: str,
        origin: str | list[str],
    ) -> None:
        self.rp_id = rp_id
        self.rp_name = rp_name
        self.origins: list[str] = [origin] if isinstance(origin, str) else list(origin)
