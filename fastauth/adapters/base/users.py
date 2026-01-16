"""
User adapter interface.

Defines the abstract interface for user account database operations.
Handles user creation, retrieval, authentication, and account management.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any


class UserAdapter(ABC):
    """
    Abstract base class for user database operations.

    Implementations must provide database-specific logic for user management.
    The core business logic remains database-agnostic.
    """

    @abstractmethod
    def get_by_email(self, email: str) -> Any:
        """
        Retrieve a user by email address.

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        ...

    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> Any:
        """
        Retrieve a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User object if found, None otherwise
        """
        ...

    @abstractmethod
    def create_user(self, *, email: str, hashed_password: str) -> Any:
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
    def set_password(self, *, user_id: uuid.UUID, hashed_password: str) -> None:
        """
        Update user's password.

        Args:
            user_id: User's unique identifier
            hashed_password: Already hashed password
        """
        ...

    @abstractmethod
    def update_last_login(self, user_id: uuid.UUID) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User's unique identifier
        """
        ...

    @abstractmethod
    def update_email(self, *, user_id: uuid.UUID, new_email: str) -> None:
        """
        Update user's email address.

        Args:
            user_id: User's unique identifier
            new_email: New email address
        """
        ...

    @abstractmethod
    def soft_delete_user(self, *, user_id: uuid.UUID) -> None:
        """
        Soft delete a user by setting deleted_at timestamp.

        Args:
            user_id: User's unique identifier
        """
        ...

    @abstractmethod
    def hard_delete_user(self, *, user_id: uuid.UUID) -> None:
        """
        Permanently delete a user from the database.

        Args:
            user_id: User's unique identifier
        """
        ...
