# OPUS 交接包（2026-02-17）

## 0. 交接目标

你将接手并继续把 `ai-job-helper` 从 Beta 推进到可增长、可融资的产品阶段。

## 1. 当前结论（先看）

- 产品状态：`Beta 可用`，尚未达到“可放量增长”标准。
- 主因：
  1. 中国真实岗位数据源稳定性不够，线上经常 `job_provider_mode=no_real_jobs`。
  2. 部分中国网络访问 `railway.app` 域名不稳定（用户端会超时）。
- 已避免假数据：默认不再回退“搜索入口伪岗位”。

## 2. 线上信息

- 线上地址：`https://ai-job-hunter-production-2730.up.railway.app`
- 工作台：`https://ai-job-hunter-production-2730.up.railway.app/app`
- 健康接口：`/api/ready`

## 3. 最近关键提交（main）

1. `4fd3c76`
   - 新增多角色执行文档包：`docs/product_build_v2/`
2. `938731b`
   - 首页文案改为增长导向（去工程口吻）
3. `24262f3`
   - `/api/process` 升级到 v2 契约
   - 严格真实岗位过滤
   - 输出质量门禁
   - 增长埋点与 KPI 接口
4. `c6fde09`
   - 中文极简 UI 与大字号优化

## 4. 关键代码改动（请先读）

- `web_app.py`
  - 新增严格岗位过滤：入口页链接默认过滤
  - 新增 `process_response.v2` 输出结构：
    - `recommended_jobs`
    - `schema_version`
    - `quality_gate`
    - `recommendation_quality`
  - 新增公共埋点接口：`POST /api/business/event`
  - `GET /api/business/public-proof` 扩展增长 KPI 字段
- `app/services/business_service.py`
  - 新增 engagement/quality 指标聚合：
    - `job_link_clicks`
    - `result_downloads`
    - `click_to_apply_pct`
    - `quality_gate_fail_rate_pct`
- `static/app_clean.html`
  - 接入结构化岗位渲染（优先 `recommended_jobs`）
  - 新增增长看板
  - 新增埋点上报：`workspace_opened`、`resume_process_*`、`job_link_click`、`result_download`
- `static/index.html`
  - 首页改为产品价值文案（增长导向）

## 5. 新契约（必须保持）

`POST /api/process` 返回必须包含：

- `success` (bool)
- `schema_version` (string, 当前 `process_response.v2`)
- `career_analysis` (string)
- `job_recommendations` (string)
- `optimized_resume` (string)
- `interview_prep` (string)
- `mock_interview` (string)
- `job_provider_mode` (string)
- `recommended_jobs` (list)
- `quality_gate` (object)
- `recommendation_quality` (object)

## 6. 当前真实阻塞（优先级 P0）

1. 真实岗位源稳定性
- 现状：默认严格真实模式下，常返回 0 岗位。
- 要求：接入稳定企业招聘 API 或稳定云缓存推送。

2. 中国区可达性
- 现状：用户端对 `railway.app` 常超时。
- 要求：Cloudflare 前置域名（免费层）+ 自有域名。

## 7. 建议 Opus 首周执行（并行）

1. 数据源通道（P0）
- 接入企业 API（主通道）
- 做 provider 健康评分与自动切换
- 建立每日缓存灌入任务

2. 可达性（P0）
- 上 Cloudflare 前置
- 完成 DNS、SSL、回源策略

3. 增长验证（P1）
- 继续保留现有埋点
- 跑 3 个实验：首页文案、上传流程、岗位卡片排序

## 8. 验收门槛（Go/No-Go）

- 真实岗位返回率 >= 85%（核心关键词样本）
- 上传->分析成功率 >= 95%
- 无 P0/P1 未关闭缺陷
- 用户反馈闭环可持续（周更）

## 9. 测试与验证

本地已通过：
- `pytest -q` -> `19 passed`

推荐 Opus 接手后先跑：

```bash
pytest -q
python -m py_compile web_app.py app/services/business_service.py
```

线上快速检查：

```bash
curl https://ai-job-hunter-production-2730.up.railway.app/api/ready
curl -X POST https://ai-job-hunter-production-2730.up.railway.app/api/process \
  -H "Content-Type: application/json" \
  -d '{"resume":"Python FastAPI SQL Docker"}'
```

## 10. 重要注意事项

- 当前仓库是“脏工作区”（大量历史/用户本地改动），不要盲目 `reset --hard`。
- 避免恢复/覆盖用户已有本地脚本与文档。
- 对外发布前请轮换任何曾暴露的第三方密钥。

## 11. 文档入口

- 总入口：`docs/product_build_v2/README.md`
- 首周执行：`docs/product_build_v2/13_执行看板_Week1.md`
- 协作机制：`docs/product_build_v2/12_多Agent协作机制.md`

---

交接完成。Opus 可按本文件直接接管执行。
