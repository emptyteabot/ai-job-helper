from fastapi.testclient import TestClient

import web_app


client = TestClient(web_app.app)


def test_version_contract_has_success_and_provider():
    resp = client.get("/api/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert "job_data_provider" in body
    assert "app_boot_ts" in body


def test_ready_contract_has_score_and_checks():
    resp = client.get("/api/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert isinstance(body.get("score"), (int, float))
    assert isinstance(body.get("checks"), dict)
    assert "global_fallback_disabled_by_default" in body["checks"]


def test_process_empty_resume_returns_structured_error():
    resp = client.post("/api/process", json={"resume": ""})
    assert resp.status_code == 400
    body = resp.json()
    assert body["success"] is False
    assert body["code"] == "empty_resume"
