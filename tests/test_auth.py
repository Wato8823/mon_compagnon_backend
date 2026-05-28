"""
Tests des routes d'authentification.
Lancer avec : pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# ── Base de données de test (SQLite en mémoire) ───────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


# ── Tests inscription ─────────────────────────────────────────
class TestRegister:
    def test_register_responsable_success(self):
        resp = client.post("/api/v1/auth/register", json={
            "nom": "DUPONT",
            "prenom": "Jean",
            "email": "jean.dupont@test.com",
            "password": "secret123",
            "role": "responsable",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "token" in data
        assert data["user"]["email"] == "jean.dupont@test.com"
        assert data["user"]["role"] == "responsable"

    def test_register_etudiant_success(self):
        resp = client.post("/api/v1/auth/register", json={
            "nom": "MARTIN",
            "prenom": "Alice",
            "email": "alice@test.com",
            "password": "pass123",
            "role": "etudiant",
        })
        assert resp.status_code == 201

    def test_register_email_duplique(self):
        payload = {"nom": "A", "prenom": "B", "email": "dup@test.com",
                   "password": "pass123", "role": "etudiant"}
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_password_trop_court(self):
        resp = client.post("/api/v1/auth/register", json={
            "nom": "X", "prenom": "Y", "email": "x@test.com",
            "password": "12", "role": "etudiant",
        })
        assert resp.status_code == 422


# ── Tests connexion ───────────────────────────────────────────
class TestLogin:
    def _create_user(self, email="test@test.com", password="pass123"):
        client.post("/api/v1/auth/register", json={
            "nom": "Test", "prenom": "User",
            "email": email, "password": password, "role": "etudiant",
        })

    def test_login_success(self):
        self._create_user()
        resp = client.post("/api/v1/auth/login", json={
            "username": "test@test.com", "password": "pass123"
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_mauvais_mdp(self):
        self._create_user()
        resp = client.post("/api/v1/auth/login", json={
            "username": "test@test.com", "password": "mauvais"
        })
        assert resp.status_code == 401

    def test_login_email_inexistant(self):
        resp = client.post("/api/v1/auth/login", json={
            "username": "nobody@test.com", "password": "pass123"
        })
        assert resp.status_code == 401


# ── Tests profil ──────────────────────────────────────────────
class TestProfile:
    def _get_token(self, email="prof@test.com", password="pass123"):
        client.post("/api/v1/auth/register", json={
            "nom": "Prof", "prenom": "Test",
            "email": email, "password": password, "role": "responsable",
        })
        resp = client.post("/api/v1/auth/login", json={
            "username": email, "password": password
        })
        return resp.json()["token"]

    def test_get_profile(self):
        token = self._get_token()
        resp = client.get("/api/v1/auth/me",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "prof@test.com"

    def test_update_profile(self):
        token = self._get_token()
        resp = client.put("/api/v1/auth/me",
                          json={"phone1": "+237 600000000"},
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["phone1"] == "+237 600000000"

    def test_get_profile_sans_token(self):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 403
