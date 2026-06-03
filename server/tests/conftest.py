import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.models.substitute import SubstituteRelation
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password
from main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

app.state.ocr_task_manager = None


@pytest.fixture(autouse=True)
def _setup_upload_dir(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "upload_dir", upload_dir)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.rollback()
        db_session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    user = User(
        username="testuser",
        password_hash=hash_password("testpass123"),
        display_name="测试用户",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
