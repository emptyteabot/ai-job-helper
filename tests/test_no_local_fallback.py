from app.services.real_job_service import RealJobService


def test_local_dataset_not_used_by_default(monkeypatch):
    monkeypatch.setenv("JOB_DATA_PROVIDER", "auto")
    monkeypatch.delenv("ALLOW_LOCAL_JOB_FALLBACK", raising=False)
    service = RealJobService()

    # Force all real-time providers off for this unit check.
    monkeypatch.setattr(service, "_use_jooble", lambda: False)
    monkeypatch.setattr(service, "_use_openclaw", lambda: False)
    monkeypatch.setattr(service, "_use_brave", lambda: False)
    monkeypatch.setattr(service, "_use_bing", lambda: False)
    monkeypatch.setattr(service, "_use_baidu", lambda: False)

    rows = service.search_jobs(keywords=["Python"], limit=5)
    assert rows == []


def test_local_dataset_only_when_explicit_local_mode(monkeypatch):
    monkeypatch.setenv("JOB_DATA_PROVIDER", "local")
    monkeypatch.delenv("ALLOW_LOCAL_JOB_FALLBACK", raising=False)
    service = RealJobService()
    rows = service.search_jobs(keywords=["Python"], limit=5)
    assert len(rows) >= 1
