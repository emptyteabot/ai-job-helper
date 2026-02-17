# 08 DevOps SRE 运行手册

更新时间：2026-02-17
Owner：DevOps/SRE

## 1. 部署目标

- 保证 24x7 可访问
- 可快速定位故障
- 可一键回滚

## 2. 当前部署

- 应用：Railway
- 域名：`*.up.railway.app`（存在地区访问波动）

## 3. 立即优化建议

- 增加 Cloudflare 前置域名（免费层）
- 配置健康检查与可用性告警
- 关键接口监控：`/api/ready`, `/api/process`, `/api/business/public-proof`

## 4. 运行手册

故障排查顺序：
1. 访问 `/api/ready`
2. 查看部署日志
3. 检查外部岗位源超时
4. 必要时回滚上个稳定版本

## 5. SLO 建议

- 可用性：>= 99.5%
- 错误率：`/api/process` < 2%
- 恢复时间（MTTR）：< 30 分钟

## 6. 配置管理

- 密钥必须环境变量注入
- 禁止硬编码 API Key
- 发布前进行配置校验脚本
