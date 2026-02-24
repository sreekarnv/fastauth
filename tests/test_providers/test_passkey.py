from fastauth.providers.passkey import PasskeyProvider


def test_passkey_provider_single_origin():
    provider = PasskeyProvider("example.com", "My App", "https://example.com")
    assert provider.id == "passkey"
    assert provider.name == "Passkey"
    assert provider.auth_type == "passkey"
    assert provider.rp_id == "example.com"
    assert provider.rp_name == "My App"
    assert provider.origins == ["https://example.com"]


def test_passkey_provider_multiple_origins():
    origins = ["https://example.com", "http://localhost:5173"]
    provider = PasskeyProvider("example.com", "My App", origins)
    assert provider.origins == origins


def test_passkey_provider_single_origin_as_list():
    provider = PasskeyProvider("localhost", "Dev App", ["http://localhost:8000"])
    assert provider.origins == ["http://localhost:8000"]
