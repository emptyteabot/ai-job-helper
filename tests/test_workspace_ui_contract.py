from fastapi.testclient import TestClient

import web_app


client = TestClient(web_app.app)


def test_workspace_shows_mandatory_optimized_resume_block():
    resp = client.get("/app")
    assert resp.status_code == 200
    body = resp.text
    assert "Optimized Resume (Mandatory Output)" in body
    assert "<details>" not in body
