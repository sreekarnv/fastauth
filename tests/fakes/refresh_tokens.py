from fastauth.adapters.base.refresh_tokens import RefreshTokenAdapter


class FakeRefreshToken:
    def __init__(self, user_id, expires_at):
        self.user_id = user_id
        self.expires_at = expires_at
        self.revoked = False


class FakeRefreshTokenAdapter(RefreshTokenAdapter):
    def __init__(self):
        self.tokens = {}

    def create(self, *, user_id, token_hash, expires_at):
        self.tokens[token_hash] = FakeRefreshToken(user_id, expires_at)

    def get_active(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token and not token.revoked:
            return token
        return None

    def revoke(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token:
            token.revoked = True
