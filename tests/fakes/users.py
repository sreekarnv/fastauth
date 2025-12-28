import uuid
from datetime import datetime

from fastauth.adapters.base.users import UserAdapter
from fastauth.core.hashing import hash_password


class FakeUser:
    def __init__(self, email, password):
        self.id = uuid.uuid4()
        self.email = email
        self.hashed_password = hash_password(password)
        self.is_verified = False
        self.is_active = True
        self.last_login = None
        self.deleted_at = None


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

    def update_last_login(self, user_id):
        from datetime import UTC

        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(UTC)

    def update_email(self, *, user_id, new_email: str):
        user = self.get_by_id(user_id)
        if user:
            old_email = user.email
            user.email = new_email
            user.is_verified = False
            if old_email in self.users:
                del self.users[old_email]
            self.users[new_email] = user

    def soft_delete_user(self, *, user_id):
        from datetime import UTC

        user = self.get_by_id(user_id)
        if user:
            user.deleted_at = datetime.now(UTC)
            user.is_active = False

    def hard_delete_user(self, *, user_id):
        user = self.get_by_id(user_id)
        if user:
            if user.email in self.users:
                del self.users[user.email]
