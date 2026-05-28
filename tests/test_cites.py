"""Tests des routes cités et chambres."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cites.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL,
                            connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


def _register_and_login(role="responsable", email="resp@test.com"):
    client.post("/api/v1/auth/register", json={
        "nom": "RESP", "prenom": "Test",
        "email": email, "password": "pass123", "role": role,
    })
    r = client.post("/api/v1/auth/login",
                    json={"username": email, "password": "pass123"})
    return r.json()["token"]


# ── Tests cités ───────────────────────────────────────────────
class TestCites:
    def test_create_cite(self):
        token = _register_and_login()
        resp = client.post("/api/v1/cites",
                           json={"nom": "La Citadelle", "description": "Test",
                                 "lieu": "PK19", "localisation": "0,0"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        assert resp.json()["nom"] == "La Citadelle"

    def test_list_cites(self):
        token = _register_and_login()
        client.post("/api/v1/cites",
                    json={"nom": "Test Cité", "description": "", "lieu": "", "localisation": ""},
                    headers={"Authorization": f"Bearer {token}"})
        resp = client.get("/api/v1/cites",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_update_cite(self):
        token = _register_and_login()
        cr = client.post("/api/v1/cites",
                         json={"nom": "Ancienne", "description": "", "lieu": "", "localisation": ""},
                         headers={"Authorization": f"Bearer {token}"})
        cite_id = cr.json()["id"]
        resp = client.put(f"/api/v1/cites/{cite_id}",
                          json={"nom": "Nouvelle"},
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Nouvelle"

    def test_delete_cite(self):
        token = _register_and_login()
        cr = client.post("/api/v1/cites",
                         json={"nom": "À supprimer", "description": "", "lieu": "", "localisation": ""},
                         headers={"Authorization": f"Bearer {token}"})
        cite_id = cr.json()["id"]
        resp = client.delete(f"/api/v1/cites/{cite_id}",
                             headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_etudiant_ne_peut_pas_creer_cite(self):
        token = _register_and_login(role="etudiant", email="etu@test.com")
        resp = client.post("/api/v1/cites",
                           json={"nom": "X", "description": "", "lieu": "", "localisation": ""},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


# ── Tests chambres ────────────────────────────────────────────
class TestChambres:
    def _create_cite(self, token):
        r = client.post("/api/v1/cites",
                        json={"nom": "Cite", "description": "", "lieu": "", "localisation": ""},
                        headers={"Authorization": f"Bearer {token}"})
        return r.json()["id"]

    def test_create_chambre(self):
        token = _register_and_login()
        cite_id = self._create_cite(token)
        resp = client.post(f"/api/v1/cites/{cite_id}/chambres",
                           json={"nom": "Ch1", "description": "Test",
                                 "equipee": True, "prix": 25000,
                                 "niveau": 1, "etat": "libre"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        assert resp.json()["nom"] == "Ch1"
        assert resp.json()["etat"] == "libre"

    def test_list_chambres(self):
        token = _register_and_login()
        cite_id = self._create_cite(token)
        client.post(f"/api/v1/cites/{cite_id}/chambres",
                    json={"nom": "Ch1", "description": "", "equipee": False,
                          "prix": 10000, "niveau": 0, "etat": "libre"},
                    headers={"Authorization": f"Bearer {token}"})
        resp = client.get(f"/api/v1/cites/{cite_id}/chambres",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1
