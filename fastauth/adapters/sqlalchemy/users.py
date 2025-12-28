from sqlmodel import Session, select

from fastauth.adapters.base.users import UserAdapter
from fastauth.adapters.sqlalchemy.models import User


class SQLAlchemyUserAdapter(UserAdapter):
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User:
        return self.session.exec(select(User).where(User.email == email)).first()

    def get_by_id(self, user_id) -> User:
        return self.session.get(User, user_id)

    def create_user(self, *, email: str, hashed_password: str) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
        )
        self.session.add(user)
        self.session.commit()
        return user

    def mark_verified(self, user_id) -> None:
        user = self.get_by_id(user_id)
        if user:
            user.is_verified = True
            self.session.add(user)
            self.session.commit()

    def set_password(self, *, user_id, hashed_password: str) -> None:
        user = self.get_by_id(user_id)
        if not user:
            return

        user.hashed_password = hashed_password
        self.session.add(user)
        self.session.commit()

    def update_last_login(self, user_id) -> None:
        from datetime import UTC, datetime

        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(UTC)
            self.session.add(user)
            self.session.commit()

    def update_email(self, *, user_id, new_email: str) -> None:
        user = self.get_by_id(user_id)
        if user:
            user.email = new_email
            user.is_verified = False
            self.session.add(user)
            self.session.commit()

    def soft_delete_user(self, *, user_id) -> None:
        from datetime import UTC, datetime

        user = self.get_by_id(user_id)
        if user:
            user.deleted_at = datetime.now(UTC)
            user.is_active = False
            self.session.add(user)
            self.session.commit()

    def hard_delete_user(self, *, user_id) -> None:
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
