"""Create a user: python -m database.create_user <login> [--role admin|user].

The password is read from USER_PASSWORD, or asked for when it is not set.
"""

import argparse
import asyncio
import getpass
import os

from database.models import User
from database.session import SessionFactory
from services.auth import hash_password


async def create_user(login: str, password: str, role: str) -> None:
    async with SessionFactory.begin() as session:
        session.add(User(login=login, password_hash=hash_password(password), role=role))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Backend user.")
    parser.add_argument("login")
    parser.add_argument("--role", choices=["admin", "user"], default="admin")
    args = parser.parse_args()
    password = os.environ.get("USER_PASSWORD") or getpass.getpass()
    asyncio.run(create_user(args.login, password, args.role))


if __name__ == "__main__":
    main()
