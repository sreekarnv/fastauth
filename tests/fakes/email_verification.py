from fastauth.adapters.base.email_verification import EmailVerificationAdapter


class FakeEmailVerification:
    def __init__(self, user_id, expires_at):
        self.user_id = user_id
        self.expires_at = expires_at
        self.used = False


class FakeEmailVerificationAdapter(EmailVerificationAdapter):
    def __init__(self):
        self.tokens = {}

    def create(self, *, user_id, token_hash, expires_at):
        self.tokens[token_hash] = FakeEmailVerification(user_id, expires_at)

    def get_valid(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token and not token.used:
            return token
        return None

    def invalidate(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token:
            token.used = True
