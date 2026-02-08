# 文档索引（最新）

如果你只想把 MVP 跑起来，只看这三份：

- `docs/howto/OPENCLAW_BOSS_MVP.md`：本机 OpenClaw + Boss 实时抓岗位链接（手动投递）
- `docs/howto/快速上手.md`：本地启动与基本用法
- `docs/deploy/云端部署指南.md`：云端 24h 部署（注意云端不支持 OpenClaw）

## 当前“真实情况”（以代码为准）

- AI 分析：`/api/process`（DeepSeek，需要 `DEEPSEEK_API_KEY`）
- 实时岗位链接：
  - 本机：`JOB_DATA_PROVIDER=openclaw`（会驱动你已 attach 的 Chrome 标签页）
  - 云端：只能做“打开招聘网站搜索链接”，不应启用 OpenClaw
- 投递：当前是“跳转投递链接 + 记录投递记录”，不会假装已自动提交

## 目录说明

- `docs/howto/`：用户使用手册
- `docs/deploy/`：部署相关
- `docs/architecture/`：架构、数据源、对接方案
- `docs/legacy/`：历史交付/融资/修复记录（保留但不作为当前使用指南）

