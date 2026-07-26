"""User data access."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db_models import User


def get_by_username(db: Session, username: str) -> User | None:
    return db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create(
    db: Session,
    *,
    username: str,
    email: str,
    hashed_password: str,
    role: str = "analyst",
) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def count(db: Session) -> int:
    return db.query(User).count()
