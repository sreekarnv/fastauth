from fastauth.core.identity import normalize_email


def test_normalize_email_trims_and_casefolds():
    assert normalize_email("  User@Example.COM  ") == "user@example.com"
