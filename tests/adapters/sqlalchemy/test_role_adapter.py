import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from fastauth.adapters.sqlalchemy.roles import SQLAlchemyRoleAdapter
from fastauth.adapters.sqlalchemy.users import SQLAlchemyUserAdapter


def test_create_role(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    role = adapter.create_role(name="admin", description="Administrator role")

    assert role.id is not None
    assert role.name == "admin"
    assert role.description == "Administrator role"
    assert role.created_at is not None


def test_get_role_by_name(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    created_role = adapter.create_role(name="admin", description="Administrator role")

    retrieved_role = adapter.get_role_by_name("admin")

    assert retrieved_role is not None
    assert retrieved_role.id == created_role.id
    assert retrieved_role.name == "admin"


def test_get_role_by_name_not_found(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    role = adapter.get_role_by_name("nonexistent")

    assert role is None


def test_unique_role_name_constraint(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    adapter.create_role(name="admin", description="First")

    with pytest.raises(IntegrityError):
        adapter.create_role(name="admin", description="Duplicate")


def test_create_permission(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    permission = adapter.create_permission(
        name="read:users", description="Read user data"
    )

    assert permission.id is not None
    assert permission.name == "read:users"
    assert permission.description == "Read user data"
    assert permission.created_at is not None


def test_get_permission_by_name(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    created_permission = adapter.create_permission(
        name="read:users", description="Read user data"
    )

    retrieved_permission = adapter.get_permission_by_name("read:users")

    assert retrieved_permission is not None
    assert retrieved_permission.id == created_permission.id
    assert retrieved_permission.name == "read:users"


def test_get_permission_by_name_not_found(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    permission = adapter.get_permission_by_name("nonexistent")

    assert permission is None


def test_unique_permission_name_constraint(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    adapter.create_permission(name="read:users", description="First")

    with pytest.raises(IntegrityError):
        adapter.create_permission(name="read:users", description="Duplicate")


def test_assign_role_to_user(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="admin")

    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)

    user_roles = role_adapter.get_user_roles(user_id=user.id)
    assert len(user_roles) == 1
    assert user_roles[0].name == "admin"


def test_assign_role_to_user_idempotent(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="admin")

    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)

    user_roles = role_adapter.get_user_roles(user_id=user.id)
    assert len(user_roles) == 1


def test_remove_role_from_user(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="admin")

    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)
    role_adapter.remove_role_from_user(user_id=user.id, role_id=role.id)

    user_roles = role_adapter.get_user_roles(user_id=user.id)
    assert len(user_roles) == 0


def test_remove_role_from_user_idempotent(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="admin")

    role_adapter.remove_role_from_user(user_id=user.id, role_id=role.id)

    user_roles = role_adapter.get_user_roles(user_id=user.id)
    assert len(user_roles) == 0


def test_get_user_roles_multiple(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")
    admin_role = role_adapter.create_role(name="admin")
    moderator_role = role_adapter.create_role(name="moderator")

    role_adapter.assign_role_to_user(user_id=user.id, role_id=admin_role.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=moderator_role.id)

    user_roles = role_adapter.get_user_roles(user_id=user.id)
    role_names = {role.name for role in user_roles}

    assert len(user_roles) == 2
    assert role_names == {"admin", "moderator"}


def test_get_user_roles_nonexistent_user(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    user_roles = adapter.get_user_roles(user_id=uuid.uuid4())

    assert len(user_roles) == 0


def test_assign_permission_to_role(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    role = adapter.create_role(name="admin")
    permission = adapter.create_permission(name="read:users")

    adapter.assign_permission_to_role(role_id=role.id, permission_id=permission.id)

    role_permissions = adapter.get_role_permissions(role_id=role.id)
    assert len(role_permissions) == 1
    assert role_permissions[0].name == "read:users"


def test_assign_permission_to_role_idempotent(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    role = adapter.create_role(name="admin")
    permission = adapter.create_permission(name="read:users")

    adapter.assign_permission_to_role(role_id=role.id, permission_id=permission.id)
    adapter.assign_permission_to_role(role_id=role.id, permission_id=permission.id)

    role_permissions = adapter.get_role_permissions(role_id=role.id)
    assert len(role_permissions) == 1


def test_get_role_permissions_multiple(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    role = adapter.create_role(name="admin")
    read_permission = adapter.create_permission(name="read:users")
    write_permission = adapter.create_permission(name="write:users")

    adapter.assign_permission_to_role(role_id=role.id, permission_id=read_permission.id)
    adapter.assign_permission_to_role(
        role_id=role.id, permission_id=write_permission.id
    )

    role_permissions = adapter.get_role_permissions(role_id=role.id)
    permission_names = {perm.name for perm in role_permissions}

    assert len(role_permissions) == 2
    assert permission_names == {"read:users", "write:users"}


def test_get_role_permissions_nonexistent_role(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    role_permissions = adapter.get_role_permissions(role_id=uuid.uuid4())

    assert len(role_permissions) == 0


def test_get_user_permissions(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")
    role = role_adapter.create_role(name="admin")
    permission = role_adapter.create_permission(name="read:users")

    role_adapter.assign_permission_to_role(role_id=role.id, permission_id=permission.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=role.id)

    user_permissions = role_adapter.get_user_permissions(user_id=user.id)
    assert len(user_permissions) == 1
    assert user_permissions[0].name == "read:users"


def test_get_user_permissions_multiple_roles(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")

    admin_role = role_adapter.create_role(name="admin")
    moderator_role = role_adapter.create_role(name="moderator")

    read_permission = role_adapter.create_permission(name="read:users")
    write_permission = role_adapter.create_permission(name="write:users")
    delete_permission = role_adapter.create_permission(name="delete:users")

    role_adapter.assign_permission_to_role(
        role_id=admin_role.id, permission_id=read_permission.id
    )
    role_adapter.assign_permission_to_role(
        role_id=admin_role.id, permission_id=write_permission.id
    )
    role_adapter.assign_permission_to_role(
        role_id=moderator_role.id, permission_id=delete_permission.id
    )

    role_adapter.assign_role_to_user(user_id=user.id, role_id=admin_role.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=moderator_role.id)

    user_permissions = role_adapter.get_user_permissions(user_id=user.id)
    permission_names = {perm.name for perm in user_permissions}

    assert len(user_permissions) == 3
    assert permission_names == {"read:users", "write:users", "delete:users"}


def test_get_user_permissions_no_duplicates(session: Session):
    role_adapter = SQLAlchemyRoleAdapter(session)
    user_adapter = SQLAlchemyUserAdapter(session)

    user = user_adapter.create_user(email="test@example.com", hashed_password="hashed")

    admin_role = role_adapter.create_role(name="admin")
    moderator_role = role_adapter.create_role(name="moderator")
    read_permission = role_adapter.create_permission(name="read:users")

    role_adapter.assign_permission_to_role(
        role_id=admin_role.id, permission_id=read_permission.id
    )
    role_adapter.assign_permission_to_role(
        role_id=moderator_role.id, permission_id=read_permission.id
    )

    role_adapter.assign_role_to_user(user_id=user.id, role_id=admin_role.id)
    role_adapter.assign_role_to_user(user_id=user.id, role_id=moderator_role.id)

    user_permissions = role_adapter.get_user_permissions(user_id=user.id)

    assert len(user_permissions) == 1
    assert user_permissions[0].name == "read:users"


def test_get_user_permissions_nonexistent_user(session: Session):
    adapter = SQLAlchemyRoleAdapter(session)

    user_permissions = adapter.get_user_permissions(user_id=uuid.uuid4())

    assert len(user_permissions) == 0
