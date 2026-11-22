from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import IntegrityError

from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import Settings, get_settings
from app.models import User
from app.repositories import get_user_repo
from app.repositories.user_repo import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, users: UserRepository, settings: Settings):
        self.users = users
        self.settings = settings

    def register(self, email: str, password: str) -> User:
        if self.users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(email=email.lower(), hashed_password=hash_password(password))
        try:
            self.users.add(user)
            self.users.db.commit()
            self.users.db.refresh(user)
        except IntegrityError as exc:
            self.users.db.rollback()
            raise EmailAlreadyRegisteredError from exc
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError
        return user

    def create_token(self, user: User) -> str:
        return create_access_token(user.id, settings=self.settings)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(users, settings)
