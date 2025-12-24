from abc import ABC, abstractmethod
import uuid


class UserAdapter(ABC):
    @abstractmethod
    def get_by_email(self, email: str):
        ...

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID):
        ...

    @abstractmethod
    def create_user(self, *, email: str, hashed_password: str):
        ...

    @abstractmethod
    def mark_verified(self, user_id: uuid.UUID) -> None:
        ...

    @abstractmethod
    def set_password(self, *, user_id, new_password: str) -> None:
        ...

