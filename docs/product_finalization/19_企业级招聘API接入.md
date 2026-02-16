# 企业级招聘 API 接入说明

## 目标

在搜索引擎回退不稳定时，优先使用企业级招聘 API，增强云端稳定性与数据可信度。

## 环境变量

- `ENTERPRISE_JOB_API_URL`：企业 API 地址（必填）
- `ENTERPRISE_JOB_API_KEY`：API Key（可选）
- `ENTERPRISE_JOB_API_METHOD`：`GET` 或 `POST`（默认 `GET`）
- `ENTERPRISE_JOB_API_AUTH_HEADER`：鉴权头名称（默认 `Authorization`）
- `ENTERPRISE_JOB_API_AUTH_SCHEME`：鉴权前缀（默认 `Bearer`）
- `ENTERPRISE_JOB_API_TIMEOUT_S`：请求超时秒数（默认 `15`）

## 回退顺序

1. 主数据源（当前 provider）
2. 企业级招聘 API（`enterprise_api`）
3. Bing HTML
4. DuckDuckGo HTML
5. 中国站点入口回退（`cn_portal`）

## 上线验收

- `/api/ready` 中 `enterprise_api_configured=true`
- `/api/jobs/search` 在风控场景可返回 `provider_mode=enterprise_api`
- 返回岗位链接必须为可点击链接
