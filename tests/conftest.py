import os

os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "test"
os.environ["DB_USER"] = "test"
os.environ["DB_PASSWORD"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-must-be-long-enough-for-validation-1234567890"
os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["SECURITY_HEADERS_ENABLED"] = "false"
os.environ["CORS_ORIGINS"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _signup_payload(email: str, password: str = "password123", name: str = "Test"):
    return {"name": name, "email": email, "password": password}


def signup(client: TestClient, email: str, password: str = "password123", name: str = "Test"):
    r = client.post("/api/v1/auth/signup", json=_signup_payload(email, password, name))
    assert r.status_code == 201, r.text
    return r


def login(client: TestClient, email: str, password: str = "password123"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r


@pytest.fixture
def auth_client(client):
    signup(client, "alice@example.com")
    return client


@pytest.fixture
def make_user(db_session):
    def _make(email: str, password: str = "password123", name: str = "User") -> User:
        user = User(name=name, email=email, password_hash=hash_password(password))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make
