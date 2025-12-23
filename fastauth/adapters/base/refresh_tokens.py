from abc import ABC, abstractmethod
from datetime import datetime
import uuid


class RefreshTokenAdapter(ABC):
    @abstractmethod
    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        ...

    @abstractmethod
    def get_active(self, *, token_hash: str):
        ...

    @abstractmethod
    def revoke(self, *, token_hash: str) -> None:
        ...
