from __future__ import annotations

import time

from cuid2 import cuid_wrapper
from joserfc.jwk import RSAKey

from fastauth.config import JWTConfig

generate_kid = cuid_wrapper()


class JWKSManager:
    def __init__(self, config: JWTConfig) -> None:
        self._config = config
        self._keys: list[tuple[RSAKey, str, float]] = []  # (key, kid, created_at)
        self._current_kid: str | None = None

    async def initialize(self) -> None:
        if self._config.private_key and self._config.public_key:
            self._load_pem_keys()
        else:
            await self.rotate()

    def _load_pem_keys(self) -> None:
        kid = generate_kid()
        assert self._config.private_key is not None
        key = RSAKey.import_key(self._config.private_key)

        key_dict = key.as_dict(private=True)
        key_dict["kid"] = kid
        key = RSAKey.import_key(key_dict)
        self._keys.append((key, kid, time.time()))
        self._current_kid = kid

    async def rotate(self) -> None:
        kid = generate_kid()
        key = RSAKey.generate_key(2048)
        key_dict = key.as_dict(private=True)
        key_dict["kid"] = kid
        key = RSAKey.import_key(key_dict)

        self._keys.append((key, kid, time.time()))
        self._current_kid = kid
        self._prune_old_keys()

    def _prune_old_keys(self) -> None:
        interval = self._config.key_rotation_interval
        if not interval or len(self._keys) <= 1:
            return
        grace = interval * 2
        cutoff = time.time() - grace
        self._keys = [
            (k, kid, ts)
            for k, kid, ts in self._keys
            if ts > cutoff or kid == self._current_kid
        ]

    def get_signing_key(self) -> RSAKey:
        for key, kid, _ in self._keys:
            if kid == self._current_kid:
                return key
        raise RuntimeError("No signing key available")

    def get_signing_kid(self) -> str:
        if not self._current_kid:
            raise RuntimeError("No signing key available")
        return self._current_kid

    def get_jwks(self) -> dict:
        keys = []
        for key, kid, _ in self._keys:
            pub = key.as_dict(private=False)
            pub["kid"] = kid
            pub["use"] = "sig"
            pub["alg"] = self._config.algorithm
            keys.append(pub)
        return {"keys": keys}

    def get_verification_keys(self) -> list[RSAKey]:
        return [key for key, _, _ in self._keys]
