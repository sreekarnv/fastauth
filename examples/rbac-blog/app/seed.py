"""Seed database with roles, permissions, and test users."""

from sqlmodel import Session

from fastauth.adapters.sqlalchemy import SQLAlchemyRoleAdapter, SQLAlchemyUserAdapter
from fastauth.core.roles import (
    assign_permission_to_role,
    assign_role,
    create_permission,
    create_role,
)
from fastauth.core.users import create_user

from .database import create_db_and_tables, engine


def seed_database():
    """Seed the database with initial data."""
    print("Seeding database...")

    create_db_and_tables()

    with Session(engine) as session:
        role_adapter = SQLAlchemyRoleAdapter(session)
        user_adapter = SQLAlchemyUserAdapter(session)

        print("\nCreating permissions...")
        permissions = [
            ("create_post", "Create new blog posts"),
            ("edit_post", "Edit existing blog posts"),
            ("publish_post", "Publish or unpublish blog posts"),
            ("delete_post", "Delete blog posts"),
        ]

        for perm_name, perm_desc in permissions:
            try:
                create_permission(
                    roles=role_adapter,
                    name=perm_name,
                    description=perm_desc,
                )
                print(f"Created permission: {perm_name}")
            except Exception:
                print(f"Permission {perm_name} already exists")

        print("\nCreating roles...")
        roles = [
            ("viewer", "Can view published blog posts"),
            ("editor", "Can create and edit blog posts"),
            ("admin", "Full access to all blog features"),
        ]

        for role_name, role_desc in roles:
            try:
                create_role(
                    roles=role_adapter,
                    name=role_name,
                    description=role_desc,
                )
                print(f"Created role: {role_name}")
            except Exception:
                print(f"Role {role_name} already exists")

        print("\nAssigning permissions to roles...")

        role_permissions = {
            "editor": ["create_post", "edit_post"],
            "admin": ["create_post", "edit_post", "publish_post", "delete_post"],
        }

        for role_name, perms in role_permissions.items():
            for perm_name in perms:
                try:
                    assign_permission_to_role(
                        roles=role_adapter,
                        role_name=role_name,
                        permission_name=perm_name,
                    )
                    print(f"Assigned {perm_name} to {role_name}")
                except Exception:
                    print(f"{perm_name} already assigned to {role_name}")

        session.commit()

        print("\nCreating test users...")
        test_users = [
            ("viewer@example.com", "password123", "viewer"),
            ("editor@example.com", "password123", "editor"),
            ("admin@example.com", "password123", "admin"),
        ]

        for email, password, role_name in test_users:
            try:
                existing_user = user_adapter.get_by_email(email=email)
                if existing_user:
                    print(f"User {email} already exists")
                    user = existing_user
                else:
                    user = create_user(
                        users=user_adapter,
                        email=email,
                        password=password,
                    )
                    print(f"Created user: {email}")

                try:
                    assign_role(
                        roles=role_adapter,
                        user_id=user.id,
                        role_name=role_name,
                    )
                    print(f"Assigned role: {role_name}")
                except Exception:
                    print(f"Role {role_name} already assigned")

                session.commit()

            except Exception as e:
                print(f"Error creating user {email}: {str(e)}")
                session.rollback()

    print("\nTest Accounts:")
    print("=" * 60)
    print("Viewer:  viewer@example.com  | password123")
    print("Editor:  editor@example.com  | password123")
    print("Admin:   admin@example.com   | password123")
    print("=" * 60)
    print("\nYou can now start the app with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    seed_database()
