from fastauth.adapters.base.password_reset import PasswordResetAdapter


class FakePasswordReset:
    def __init__(self, user_id, expires_at):
        self.user_id = user_id
        self.expires_at = expires_at
        self.used = False


class FakePasswordResetAdapter(PasswordResetAdapter):
    def __init__(self):
        self.tokens = {}

    def create(self, *, user_id, token_hash, expires_at):
        self.tokens[token_hash] = FakePasswordReset(user_id, expires_at)

    def get_valid(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token and not token.used:
            return token
        return None

    def mark_used(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token:
            token.used = True
