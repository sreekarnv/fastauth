from fastauth.core.credentials import hash_password, verify_password


def test_hash_and_verify_password():
    password = "mysecretpassword"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_verify_wrong_password():
    hashed_password = hash_password("correct")

    assert verify_password("wrong", hashed_password) is False


def test_hash_produces_different_hashes():
    password = "mysecretpassword"

    hash_1 = hash_password(password)
    hash_2 = hash_password(password)

    assert not hash_1 == hash_2
