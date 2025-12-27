import uuid
from abc import ABC, abstractmethod


class RoleAdapter(ABC):
    """
    Abstract base class for role and permission database operations.

    Implementations must provide database-specific logic for RBAC.
    The core business logic remains database-agnostic.
    """

    @abstractmethod
    def create_role(self, *, name: str, description: str | None = None):
        """
        Create a new role.

        Args:
            name: Unique role name
            description: Optional role description

        Returns:
            Created role object
        """
        ...

    @abstractmethod
    def get_role_by_name(self, name: str):
        """
        Retrieve a role by name.

        Args:
            name: Role name

        Returns:
            Role object if found, None otherwise
        """
        ...

    @abstractmethod
    def create_permission(self, *, name: str, description: str | None = None):
        """
        Create a new permission.

        Args:
            name: Unique permission name
            description: Optional permission description

        Returns:
            Created permission object
        """
        ...

    @abstractmethod
    def get_permission_by_name(self, name: str):
        """
        Retrieve a permission by name.

        Args:
            name: Permission name

        Returns:
            Permission object if found, None otherwise
        """
        ...

    @abstractmethod
    def assign_role_to_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        """
        Assign a role to a user.

        Args:
            user_id: User's unique identifier
            role_id: Role's unique identifier
        """
        ...

    @abstractmethod
    def remove_role_from_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        """
        Remove a role from a user.

        Args:
            user_id: User's unique identifier
            role_id: Role's unique identifier
        """
        ...

    @abstractmethod
    def get_user_roles(self, user_id: uuid.UUID):
        """
        Get all roles assigned to a user.

        Args:
            user_id: User's unique identifier

        Returns:
            List of role objects
        """
        ...

    @abstractmethod
    def assign_permission_to_role(
        self, *, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        """
        Assign a permission to a role.

        Args:
            role_id: Role's unique identifier
            permission_id: Permission's unique identifier
        """
        ...

    @abstractmethod
    def get_role_permissions(self, role_id: uuid.UUID):
        """
        Get all permissions assigned to a role.

        Args:
            role_id: Role's unique identifier

        Returns:
            List of permission objects
        """
        ...

    @abstractmethod
    def get_user_permissions(self, user_id: uuid.UUID):
        """
        Get all permissions for a user (from all their roles).

        Args:
            user_id: User's unique identifier

        Returns:
            List of permission objects
        """
        ...
