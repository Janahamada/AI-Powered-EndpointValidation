"""
Seed the default admin user if the users table is empty.

    python backend/scripts/seed_users.py

Credentials come from settings (DEFAULT_ADMIN_*), overridable via env. This is
idempotent: it never creates a duplicate and never overwrites an existing user.
"""

import _bootstrap  # noqa: F401

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.repositories import user_repo


def main() -> None:
    with SessionLocal() as db:
        existing = user_repo.get_by_username(db, settings.DEFAULT_ADMIN_USERNAME)
        if existing:
            print(f"User '{settings.DEFAULT_ADMIN_USERNAME}' already exists — skipping.")
            return
        user_repo.create(
            db,
            username=settings.DEFAULT_ADMIN_USERNAME,
            email=settings.DEFAULT_ADMIN_EMAIL,
            hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            role="admin",
        )
    print(
        f"Seeded admin user '{settings.DEFAULT_ADMIN_USERNAME}' "
        f"(password: '{settings.DEFAULT_ADMIN_PASSWORD}' — change in production)."
    )


if __name__ == "__main__":
    main()
