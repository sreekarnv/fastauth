"""
SQLAlchemy OAuth state adapter implementation.

Provides database operations for OAuth state token storage using SQLAlchemy/SQLModel.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from fastauth.adapters.base.oauth_states import OAuthStateAdapter
from fastauth.adapters.sqlalchemy.models import OAuthState


class SQLAlchemyOAuthStateAdapter(OAuthStateAdapter):
    """
    SQLAlchemy implementation of OAuthStateAdapter.
    """

    def __init__(self, session: Session):
        self.session = session

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
        state = OAuthState(
            state_hash=state_hash,
            provider=provider,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.session.add(state)
        self.session.commit()
        self.session.refresh(state)
        return state

    def get_valid(self, *, state_hash: str):
        return self.session.exec(
            select(OAuthState).where(
                OAuthState.state_hash == state_hash,
                OAuthState.used == False,  # noqa: E712
            )
        ).first()

    def mark_used(self, *, state_hash: str) -> None:
        state = self.get_valid(state_hash=state_hash)
        if state:
            state.used = True
            self.session.add(state)
            self.session.commit()

    def cleanup_expired(self) -> None:
        statement = select(OAuthState).where(OAuthState.expires_at < datetime.now(UTC))
        expired_states = self.session.exec(statement).all()
        for state in expired_states:
            self.session.delete(state)
        self.session.commit()
