import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class EmailVerificationAdapter(ABC):
    @abstractmethod
    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...

    @abstractmethod
    def get_valid(self, *, token_hash: str): ...

    @abstractmethod
    def mark_used(self, *, token_hash: str) -> None: ...
