"""Tests for the FastAPI layer: parameter passthrough and API-key auth."""

from fastapi.testclient import TestClient

import api
import config


PAYLOAD = {
    "participants": [
        {"name": "A", "address": "a", "mode": "driving"},
        {"name": "B", "address": "b"},
    ],
    "keywords": "火锅",
    "max_cost": 100,
    "top_k": 2,
}


def make_client(monkeypatch, captured):
    def fake_skill(**kwargs):
        captured.update(kwargs)
        return {"places": [], **kwargs}

    monkeypatch.setattr(api, "run_gathere_skill", fake_skill)
    return TestClient(api.app)


def test_recommend_passthrough(monkeypatch):
    captured = {}
    client = make_client(monkeypatch, captured)

    response = client.post("/recommend", json=PAYLOAD)

    assert response.status_code == 200
    assert captured["max_cost"] == 100
    assert captured["top_k"] == 2
    # Per-participant mode survives; participant B has no mode key.
    assert captured["participants"][0] == {"name": "A", "address": "a", "mode": "driving"}
    assert captured["participants"][1] == {"name": "B", "address": "b"}


def test_auth_disabled_by_default(monkeypatch):
    monkeypatch.setattr(config, "GATHERE_API_KEY", "")
    captured = {}
    client = make_client(monkeypatch, captured)

    assert client.post("/recommend", json=PAYLOAD).status_code == 200


def test_auth_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(config, "GATHERE_API_KEY", "secret")
    captured = {}
    client = make_client(monkeypatch, captured)

    response = client.post("/recommend", json=PAYLOAD)
    assert response.status_code == 401


def test_auth_accepts_correct_key(monkeypatch):
    monkeypatch.setattr(config, "GATHERE_API_KEY", "secret")
    captured = {}
    client = make_client(monkeypatch, captured)

    response = client.post("/recommend", json=PAYLOAD, headers={"X-API-Key": "secret"})
    assert response.status_code == 200


def test_invalid_mode_rejected_by_validation(monkeypatch):
    monkeypatch.setattr(config, "GATHERE_API_KEY", "")
    captured = {}
    client = make_client(monkeypatch, captured)

    bad = {**PAYLOAD, "participants": [{"name": "A", "address": "a", "mode": "rocket"}]}
    assert client.post("/recommend", json=bad).status_code == 422
