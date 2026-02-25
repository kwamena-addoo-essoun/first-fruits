import os
import unittest.mock
from pathlib import Path

# Must be set before importing main/app so the rate limiter uses test-safe limits.
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from main import app

TEST_DB_PATH = Path(__file__).parent / "test_api.db"
SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def _no_smtp(db_session):
    """Block all real SMTP calls during every test.

    The send_verification_email mock also auto-verifies the user so that
    register_and_login() flows work without any changes to callers.
    """
    def _auto_verify(to_email, token):
        from app.models.email_verification import EmailVerificationToken
        from app.models.user import User
        record = db_session.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token
        ).first()
        if record:
            user = db_session.query(User).filter(User.id == record.user_id).first()
            if user:
                user.is_verified = True
                record.used = True
                db_session.flush()

    with unittest.mock.patch("app.routes.auth.send_verification_email", side_effect=_auto_verify):
        with unittest.mock.patch("app.routes.admin.send_password_reset_email"):
            with unittest.mock.patch("app.routes.auth.send_password_reset_email"):
                yield


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session):
    return TestClient(app)
