import uuid
from datetime import UTC, datetime

from fastauth.adapters.base.oauth_states import OAuthStateAdapter


class FakeOAuthState:
    def __init__(
        self,
        *,
        state_hash: str,
        provider: str,
        redirect_uri: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        user_id: uuid.UUID | None = None,
        expires_at: datetime,
    ):
        self.id = uuid.uuid4()
        self.state_hash = state_hash
        self.provider = provider
        self.redirect_uri = redirect_uri
        self.code_challenge = code_challenge
        self.code_challenge_method = code_challenge_method
        self.user_id = user_id
        self.expires_at = expires_at
        self.used = False
        self.created_at = datetime.now(UTC)


class FakeOAuthStateAdapter(OAuthStateAdapter):
    def __init__(self):
        self.states = {}

    def create(
        self,
        *,
        state_hash: str,
        provider: str,
        redirect_uri: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        user_id: uuid.UUID | None = None,
        expires_at: datetime,
    ):
        state = FakeOAuthState(
            state_hash=state_hash,
            provider=provider,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.states[state_hash] = state
        return state

    def get_valid(self, *, state_hash: str):
        state = self.states.get(state_hash)
        if state and not state.used:
            return state
        return None

    def mark_used(self, *, state_hash: str) -> None:
        state = self.states.get(state_hash)
        if state:
            state.used = True

    def cleanup_expired(self) -> None:
        expired_hashes = []
        for state_hash, state in self.states.items():
            if state.expires_at < datetime.now(UTC):
                expired_hashes.append(state_hash)

        for state_hash in expired_hashes:
            del self.states[state_hash]
