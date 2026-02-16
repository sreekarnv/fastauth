import time

from fastauth.config import JWTConfig
from fastauth.core.jwks import JWKSManager


async def test_initialize_generates_key():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()

    assert manager._current_kid is not None
    assert len(manager._keys) == 1


async def test_initialize_with_pem_keys():
    from joserfc.jwk import RSAKey

    key = RSAKey.generate_key(2048)
    private_pem = key.as_pem(private=True).decode()
    public_pem = key.as_pem(private=False).decode()

    config = JWTConfig(
        algorithm="RS256",
        private_key=private_pem,
        public_key=public_pem,
    )
    manager = JWKSManager(config)
    await manager.initialize()

    assert manager._current_kid is not None
    assert len(manager._keys) == 1


async def test_rotate_creates_new_key():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()
    first_kid = manager._current_kid

    await manager.rotate()

    assert manager._current_kid != first_kid
    assert len(manager._keys) == 2


async def test_get_signing_key():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()

    key = manager.get_signing_key()
    assert key is not None
    assert key.kid == manager._current_kid


async def test_get_signing_kid():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()

    kid = manager.get_signing_kid()
    assert kid == manager._current_kid


async def test_get_jwks_format():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()

    jwks = manager.get_jwks()
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1

    pub_key = jwks["keys"][0]
    assert pub_key["kty"] == "RSA"
    assert pub_key["use"] == "sig"
    assert pub_key["alg"] == "RS256"

    assert "kid" in pub_key
    assert "n" in pub_key
    assert "e" in pub_key

    assert "d" not in pub_key
    assert "p" not in pub_key
    assert "q" not in pub_key


async def test_get_jwks_after_rotation():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()
    await manager.rotate()

    jwks = manager.get_jwks()
    assert len(jwks["keys"]) == 2
    kids = {k["kid"] for k in jwks["keys"]}
    assert len(kids) == 2


async def test_get_verification_keys():
    config = JWTConfig(algorithm="RS256")
    manager = JWKSManager(config)
    await manager.initialize()
    await manager.rotate()

    keys = manager.get_verification_keys()
    assert len(keys) == 2


async def test_prune_old_keys():
    config = JWTConfig(algorithm="RS256", key_rotation_interval=3600)
    manager = JWKSManager(config)
    await manager.initialize()

    old_key, old_kid, _ = manager._keys[0]
    manager._keys[0] = (old_key, old_kid, time.time() - 8000)

    await manager.rotate()

    assert len(manager._keys) == 1
    assert manager._keys[0][1] == manager._current_kid


async def test_prune_keeps_recent_keys():
    config = JWTConfig(algorithm="RS256", key_rotation_interval=3600)
    manager = JWKSManager(config)
    await manager.initialize()

    await manager.rotate()
    assert len(manager._keys) == 2
