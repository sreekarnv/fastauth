import uuid
from abc import ABC, abstractmethod


class UserAdapter(ABC):
    """
    Abstract base class for user database operations.

    Implementations must provide database-specific logic for user management.
    The core business logic remains database-agnostic.
    """

    @abstractmethod
    def get_by_email(self, email: str):
        """
        Retrieve a user by email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        ...

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID):
        """
        Retrieve a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User object if found, None otherwise
        """
        ...

    @abstractmethod
    def create_user(self, *, email: str, hashed_password: str):
        """
        Create a new user.

        Args:
            email: User's email address
            hashed_password: Already hashed password

        Returns:
            Created user object
        """
        ...

    @abstractmethod
    def mark_verified(self, user_id: uuid.UUID) -> None:
        """
        Mark a user's email as verified.

        Args:
            user_id: User's unique identifier
        """
        ...

    @abstractmethod
    def set_password(self, *, user_id, new_password: str) -> None:
        """
        Update user's password.

        Args:
            user_id: User's unique identifier
            new_password: New hashed password
        """
        ...
