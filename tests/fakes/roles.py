import uuid
from datetime import UTC, datetime

from fastauth.adapters.base.roles import RoleAdapter


class FakeRole:
    def __init__(self, name, description=None):
        self.id = uuid.uuid4()
        self.name = name
        self.description = description
        self.created_at = datetime.now(UTC)


class FakePermission:
    def __init__(self, name, description=None):
        self.id = uuid.uuid4()
        self.name = name
        self.description = description
        self.created_at = datetime.now(UTC)


class FakeRoleAdapter(RoleAdapter):
    def __init__(self):
        self.roles = {}
        self.permissions = {}
        self.user_roles = {}
        self.role_permissions = {}

    def create_role(self, *, name: str, description: str | None = None):
        role = FakeRole(name, description)
        self.roles[name] = role
        return role

    def get_role_by_name(self, name: str):
        return self.roles.get(name)

    def create_permission(self, *, name: str, description: str | None = None):
        permission = FakePermission(name, description)
        self.permissions[name] = permission
        return permission

    def get_permission_by_name(self, name: str):
        return self.permissions.get(name)

    def assign_role_to_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role_id)

    def remove_role_from_user(self, *, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_id)

    def get_user_roles(self, user_id: uuid.UUID):
        role_ids = self.user_roles.get(user_id, set())
        return [role for role in self.roles.values() if role.id in role_ids]

    def assign_permission_to_role(
        self, *, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        if role_id not in self.role_permissions:
            self.role_permissions[role_id] = set()
        self.role_permissions[role_id].add(permission_id)

    def get_role_permissions(self, role_id: uuid.UUID):
        permission_ids = self.role_permissions.get(role_id, set())
        return [perm for perm in self.permissions.values() if perm.id in permission_ids]

    def get_user_permissions(self, user_id: uuid.UUID):
        user_roles = self.get_user_roles(user_id)
        all_permissions = set()

        for role in user_roles:
            role_perms = self.get_role_permissions(role.id)
            for perm in role_perms:
                all_permissions.add(perm.id)

        return [
            perm for perm in self.permissions.values() if perm.id in all_permissions
        ]
