import web_app


def test_ddg_redirect_normalization_supports_absolute_redirect():
    href = (
        "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.zhipin.com%2Fweb%2Fgeek%2Fjob"
        "%3Fquery%3DPython&amp;rut=abc"
    )
    url = web_app._normalize_ddg_redirect(href)
    assert url.startswith("https://www.zhipin.com/")


def test_cn_entrypoint_fallback_returns_cn_domains_only():
    rows = web_app._search_jobs_cn_entrypoints(["Python", "后端"], "北京", limit=5)
    assert len(rows) == 5
    for row in rows:
        link = (row.get("link") or "").lower()
        assert any(d in link for d in web_app.CN_JOB_DOMAINS)
        assert row.get("platform") in {"Boss直聘", "猎聘", "智联招聘", "前程无忧", "拉勾"}
