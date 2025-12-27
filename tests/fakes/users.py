import uuid

from fastauth.adapters.base.users import UserAdapter
from fastauth.core.hashing import hash_password


class FakeUser:
    def __init__(self, email, password):
        self.id = uuid.uuid4()
        self.email = email
        self.hashed_password = hash_password(password)
        self.is_verified = False
        self.is_active = True


class FakeUserAdapter(UserAdapter):
    def __init__(self):
        self.users = {}

    def get_by_email(self, email: str):
        return self.users.get(email)

    def get_by_id(self, user_id):
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None

    def create_user(self, *, email: str, hashed_password: str):
        if email in self.users:
            raise Exception("User already exists")
        user = FakeUser(email, "dummy")
        user.hashed_password = hashed_password
        self.users[email] = user
        return user

    def mark_verified(self, user_id):
        user = self.get_by_id(user_id)
        if user:
            user.is_verified = True

    def set_password(self, *, user_id, hashed_password: str):
        user = self.get_by_id(user_id)
        if user:
            user.hashed_password = hashed_password
