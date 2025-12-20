from fastauth.core.hashing import hash_password, verify_password


def test_password_hash_and_verify():
    password = "super-secret-password"

    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(hashed, password) is True
    assert verify_password(hashed, "wrong-password") is False
