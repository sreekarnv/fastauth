from sqlmodel import Session, select

from fastauth.adapters.base.users import UserAdapter
from fastauth.adapters.sqlalchemy.models import User
from fastauth.core.hashing import hash_password


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

    def set_password(self, *, user_id, new_password: str) -> None:
        user = self.get_by_id(user_id)
        if not user:
            return

        user.hashed_password = hash_password(new_password)
        self.session.add(user)
        self.session.commit()
