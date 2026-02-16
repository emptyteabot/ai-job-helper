import web_app


def test_enterprise_api_returns_empty_when_url_not_configured(monkeypatch):
    monkeypatch.delenv("ENTERPRISE_JOB_API_URL", raising=False)
    rows = web_app._search_jobs_enterprise_api(["Python"], "北京", 5)
    assert rows == []


def test_enterprise_api_maps_cn_jobs(monkeypatch):
    monkeypatch.setenv("ENTERPRISE_JOB_API_URL", "https://enterprise.example/jobs")
    monkeypatch.setenv("ENTERPRISE_JOB_API_METHOD", "GET")

    class _Resp:
        status_code = 200
        content = b"x"

        @staticmethod
        def json():
            return {
                "jobs": [
                    {
                        "title": "Python后端工程师",
                        "company": "测试科技",
                        "location": "北京",
                        "salary": "30-45K",
                        "url": "https://www.zhipin.com/job_detail/abc123.html",
                    }
                ]
            }

    def _fake_get(url, params=None, headers=None, timeout=0):
        assert "enterprise.example" in url
        return _Resp()

    monkeypatch.setattr(web_app.requests, "get", _fake_get)
    rows = web_app._search_jobs_enterprise_api(["Python"], "北京", 5)
    assert len(rows) == 1
    assert rows[0]["platform"] == "Boss直聘"
    assert "zhipin.com" in rows[0]["link"]
