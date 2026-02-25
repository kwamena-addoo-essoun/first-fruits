#!/usr/bin/env python
"""Promote a user to admin.

Usage:
    python make_admin.py <username>

Example:
    python make_admin.py alice
"""
import sys
import os

# Allow running from the backend/ directory without setting PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User


def make_admin(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"Error: user '{username}' not found.")
            sys.exit(1)
        if user.is_admin:
            print(f"'{username}' is already an admin.")
            return
        user.is_admin = True
        db.commit()
        print(f"✅ '{username}' is now an admin. They must log in again to receive admin privileges.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    make_admin(sys.argv[1])
