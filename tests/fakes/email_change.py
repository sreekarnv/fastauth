from fastauth.adapters.base.email_change import EmailChangeAdapter


class FakeEmailChange:
    def __init__(self, user_id, new_email, expires_at):
        self.user_id = user_id
        self.new_email = new_email
        self.expires_at = expires_at
        self.used = False


class FakeEmailChangeAdapter(EmailChangeAdapter):
    def __init__(self):
        self.tokens = {}

    def create(self, *, user_id, new_email, token_hash, expires_at):
        self.tokens[token_hash] = FakeEmailChange(user_id, new_email, expires_at)

    def get_valid(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token and not token.used:
            return token
        return None

    def mark_used(self, *, token_hash):
        token = self.tokens.get(token_hash)
        if token:
            token.used = True
