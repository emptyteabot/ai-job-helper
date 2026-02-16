from fastapi.testclient import TestClient

import web_app


client = TestClient(web_app.app)


def test_investor_readiness_contract():
    resp = client.get("/api/investor/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "overall_score" in body
    assert "pillars" in body
    assert "next_30d_targets" in body


def test_investor_summary_contract():
    resp = client.get("/api/investor/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body.get("narrative"), list)
    assert len(body["narrative"]) >= 1


def test_investor_page_available():
    resp = client.get("/investor")
    assert resp.status_code == 200
    assert "Investor" in resp.text
