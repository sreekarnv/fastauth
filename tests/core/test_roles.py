import uuid

import pytest

from fastauth.core.roles import (
    PermissionAlreadyExistsError,
    PermissionNotFoundError,
    RoleAlreadyExistsError,
    RoleNotFoundError,
    assign_permission_to_role,
    assign_role,
    check_permission,
    create_permission,
    create_role,
    get_role_permissions,
    get_user_permissions,
    get_user_roles,
    remove_role,
)
from tests.fakes.roles import FakeRoleAdapter


@pytest.fixture
def roles():
    return FakeRoleAdapter()


def test_create_role_success(roles):
    role = create_role(
        roles=roles,
        name="admin",
        description="Administrator role",
    )

    assert role.id is not None
    assert role.name == "admin"
    assert role.description == "Administrator role"


def test_create_role_duplicate(roles):
    create_role(roles=roles, name="admin")

    with pytest.raises(RoleAlreadyExistsError):
        create_role(roles=roles, name="admin")


def test_create_permission_success(roles):
    permission = create_permission(
        roles=roles,
        name="read:users",
        description="Read user data",
    )

    assert permission.id is not None
    assert permission.name == "read:users"
    assert permission.description == "Read user data"


def test_create_permission_duplicate(roles):
    create_permission(roles=roles, name="read:users")

    with pytest.raises(PermissionAlreadyExistsError):
        create_permission(roles=roles, name="read:users")


def test_assign_role_to_user(roles):
    user_id = uuid.uuid4()
    create_role(roles=roles, name="admin")

    assign_role(roles=roles, user_id=user_id, role_name="admin")

    user_roles = get_user_roles(roles=roles, user_id=user_id)
    assert len(user_roles) == 1
    assert user_roles[0].name == "admin"


def test_assign_role_not_found(roles):
    user_id = uuid.uuid4()

    with pytest.raises(RoleNotFoundError):
        assign_role(roles=roles, user_id=user_id, role_name="nonexistent")


def test_remove_role_from_user(roles):
    user_id = uuid.uuid4()
    create_role(roles=roles, name="admin")

    assign_role(roles=roles, user_id=user_id, role_name="admin")
    remove_role(roles=roles, user_id=user_id, role_name="admin")

    user_roles = get_user_roles(roles=roles, user_id=user_id)
    assert len(user_roles) == 0


def test_remove_role_not_found(roles):
    user_id = uuid.uuid4()

    with pytest.raises(RoleNotFoundError):
        remove_role(roles=roles, user_id=user_id, role_name="nonexistent")


def test_assign_permission_to_role_success(roles):
    create_role(roles=roles, name="admin")
    create_permission(roles=roles, name="read:users")

    assign_permission_to_role(
        roles=roles,
        role_name="admin",
        permission_name="read:users",
    )

    permissions = get_role_permissions(roles=roles, role_name="admin")
    assert len(permissions) == 1
    assert permissions[0].name == "read:users"


def test_assign_permission_to_role_role_not_found(roles):
    create_permission(roles=roles, name="read:users")

    with pytest.raises(RoleNotFoundError):
        assign_permission_to_role(
            roles=roles,
            role_name="nonexistent",
            permission_name="read:users",
        )


def test_assign_permission_to_role_permission_not_found(roles):
    create_role(roles=roles, name="admin")

    with pytest.raises(PermissionNotFoundError):
        assign_permission_to_role(
            roles=roles,
            role_name="admin",
            permission_name="nonexistent",
        )


def test_check_permission_has_permission(roles):
    user_id = uuid.uuid4()
    create_role(roles=roles, name="admin")
    create_permission(roles=roles, name="read:users")

    assign_permission_to_role(
        roles=roles, role_name="admin", permission_name="read:users"
    )
    assign_role(roles=roles, user_id=user_id, role_name="admin")

    has_permission = check_permission(
        roles=roles,
        user_id=user_id,
        permission_name="read:users",
    )

    assert has_permission is True


def test_check_permission_no_permission(roles):
    user_id = uuid.uuid4()
    create_role(roles=roles, name="admin")
    assign_role(roles=roles, user_id=user_id, role_name="admin")

    has_permission = check_permission(
        roles=roles,
        user_id=user_id,
        permission_name="read:users",
    )

    assert has_permission is False


def test_get_user_roles_multiple(roles):
    user_id = uuid.uuid4()
    create_role(roles=roles, name="admin")
    create_role(roles=roles, name="moderator")

    assign_role(roles=roles, user_id=user_id, role_name="admin")
    assign_role(roles=roles, user_id=user_id, role_name="moderator")

    user_roles = get_user_roles(roles=roles, user_id=user_id)
    role_names = {role.name for role in user_roles}

    assert len(user_roles) == 2
    assert role_names == {"admin", "moderator"}


def test_get_user_permissions_from_multiple_roles(roles):
    user_id = uuid.uuid4()

    create_role(roles=roles, name="admin")
    create_role(roles=roles, name="moderator")
    create_permission(roles=roles, name="read:users")
    create_permission(roles=roles, name="write:users")
    create_permission(roles=roles, name="delete:users")

    assign_permission_to_role(
        roles=roles, role_name="admin", permission_name="read:users"
    )
    assign_permission_to_role(
        roles=roles, role_name="admin", permission_name="write:users"
    )
    assign_permission_to_role(
        roles=roles, role_name="moderator", permission_name="delete:users"
    )

    assign_role(roles=roles, user_id=user_id, role_name="admin")
    assign_role(roles=roles, user_id=user_id, role_name="moderator")

    user_permissions = get_user_permissions(roles=roles, user_id=user_id)
    permission_names = {perm.name for perm in user_permissions}

    assert len(user_permissions) == 3
    assert permission_names == {"read:users", "write:users", "delete:users"}


def test_get_role_permissions_role_not_found(roles):
    with pytest.raises(RoleNotFoundError):
        get_role_permissions(roles=roles, role_name="nonexistent")
