from fastapi.testclient import TestClient

import web_app


client = TestClient(web_app.app)


def test_feedback_api_accepts_valid_payload():
    resp = client.post(
        "/api/business/feedback",
        json={
            "message": "UI is cleaner now, but mobile spacing can improve.",
            "rating": 4,
            "category": "ui",
            "source": "test",
            "page": "home",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "feedback_id" in body["data"]


def test_feedback_api_rejects_short_payload():
    resp = client.post("/api/business/feedback", json={"message": "bad"})
    assert resp.status_code == 400


def test_public_proof_contract():
    resp = client.get("/api/business/public-proof")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "leads_total" in body
    assert "feedback_total" in body
