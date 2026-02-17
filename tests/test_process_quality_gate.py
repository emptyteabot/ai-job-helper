import web_app


def test_normalize_real_jobs_filters_cn_entrypoint_links():
    rows = web_app._normalize_real_jobs(
        [
            {
                "id": "portal_1",
                "title": "Python - Boss直聘搜索入口",
                "provider": "cn_portal",
                "link": "https://www.zhipin.com/web/geek/job?query=Python",
            },
            {
                "id": "real_1",
                "title": "Python后端开发工程师",
                "company": "测试科技",
                "link": "https://www.zhipin.com/job_detail/abc123.html",
            },
        ],
        limit=5,
    )
    assert len(rows) == 1
    assert rows[0]["id"] == "real_1"


def test_quality_gate_replaces_foreign_or_low_quality_text():
    raw = {
        "market_analysis": "I appreciate your interest, but I'm Amazon Q.",
        "optimized_resume": "too short",
        "interview_prep": "我在当前对话中没有看到任何附件",
        "salary_analysis": "",
    }
    info = {"name": "Yinghua Chen", "skills": ["Python", "FastAPI", "SQL"]}
    jobs = [
        {
            "id": "real_2",
            "title": "Python后端开发工程师",
            "company": "测试科技",
            "link": "https://www.zhipin.com/job_detail/real2.html",
        }
    ]
    clean, report = web_app._run_output_quality_gate(raw, "resume", info, jobs)
    assert report["passed"] is False
    assert "Amazon Q" not in clean["market_analysis"]
    assert "附件" not in clean["interview_prep"]
    assert len(clean["optimized_resume"]) > 120


def test_process_response_shape_validator_accepts_v2_payload():
    payload = {
        "career_analysis": "ok",
        "job_recommendations": "ok",
        "optimized_resume": "ok",
        "interview_prep": "ok",
        "mock_interview": "ok",
        "job_provider_mode": "duckduckgo",
        "schema_version": web_app.PROCESS_RESPONSE_SCHEMA_VERSION,
        "recommended_jobs": [
            {
                "id": "job_1",
                "title": "Python后端开发工程师",
                "link": "https://www.zhipin.com/job_detail/1.html",
            }
        ],
    }
    assert web_app._validate_process_response_shape(payload) == []
