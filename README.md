# 🤖 AI求职助手 - 全球首个6AI协作求职系统

<div align="center">

![AI求职助手](https://img.shields.io/badge/AI-6个协作-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![License](https://img.shields.io/badge/License-MIT-yellow)

**让每个人都能找到理想工作**

[🚀 在线体验](https://ai-job-hunter-production-2730.up.railway.app) | [📖 文档](./docs) | [💬 讨论](https://github.com/emptyteabot/ai-job-helper/discussions)

</div>

---

## ✨ 核心特性

### 🎯 6个AI协作引擎（全球首创）

```
市场分析师 → 简历分析师 → 岗位匹配师 → 简历优化师 → 面试教练 → 职业顾问
```

不是单个AI，而是6个AI互相辩论、协作，输出最优方案！

### 🚀 端到端解决方案

- ✅ **AI简历分析** - 深度解析您的简历，找出优势和不足
- ✅ **智能岗位推荐** - 基于真实市场数据，推荐最匹配的岗位
- ✅ **简历优化** - AI帮您重写简历，提升50%竞争力
- ✅ **面试辅导** - 模拟面试，提供专业建议
- ✅ **职业规划** - 3-5年职业发展路径规划

### 📱 完美体验

- ✅ **移动端适配** - 手机、平板、电脑完美适配
- ✅ **实时进度** - WebSocket实时推送AI分析进度
- ✅ **快速响应** - 缓存优化，响应时间<2秒
- ✅ **美观界面** - 现代化设计，流畅动画

### 🔗 真实岗位对接

- ✅ **Boss直聘集成** - 真实岗位，一键跳转
- ✅ **自动投递** - AI帮您自动投递简历
- ✅ **投递追踪** - 记录每次投递，追踪进度

---

## 🎬 快速开始

### 在线体验（推荐）

访问：[https://ai-job-hunter-production-2730.up.railway.app](https://ai-job-hunter-production-2730.up.railway.app)

1. 上传简历（PDF/Word/图片）或粘贴文本
2. 点击"开始AI分析"
3. 等待1-2分钟
4. 查看完整分析报告

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/emptyteabot/ai-job-helper.git
cd ai-job-helper

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入您的 DeepSeek API Key

# 4. 启动服务
python web_app.py

# 5. 访问
# 浏览器打开 http://localhost:8000
```

---

## 📊 与竞品对比

| 功能 | Resume.io | JobSpy | AI Resume | **我们** |
|------|-----------|--------|-----------|----------|
| 简历优化 | ✅ | ❌ | ✅ | ✅ |
| AI分析 | ❌ | ❌ | ⚠️ 单AI | ✅ **6个AI** |
| 岗位推荐 | ❌ | ✅ | ❌ | ✅ |
| 自动投递 | ❌ | ❌ | ❌ | ✅ |
| 面试辅导 | ❌ | ❌ | ❌ | ✅ |
| 移动端 | ✅ | ❌ | ⚠️ | ✅ |
| 开源 | ❌ | ✅ | ✅ | ✅ |
| 价格 | $24.95/月 | 免费 | 免费 | **免费** |

**我们的优势：功能最完整 + 体验最好 + 完全免费**

---

## 🏗️ 技术架构

### 后端

- **框架：** FastAPI（高性能异步框架）
- **AI引擎：** DeepSeek（成本低、效果好）
- **数据库：** PostgreSQL（生产环境）/ SQLite（开发环境）
- **缓存：** Redis / 内存缓存
- **任务队列：** Celery（可选）

### 前端

- **纯HTML/CSS/JavaScript** - 无需构建，开箱即用
- **WebSocket** - 实时进度推送
- **响应式设计** - 完美适配所有设备
- **现代动画** - 流畅的用户体验

### 部署

- **云平台：** Railway / Vercel / AWS
- **CI/CD：** GitHub Actions自动部署
- **监控：** 内置性能监控
- **日志：** 结构化日志

---

## 🎨 截图

### 首页
![首页](./docs/screenshots/home.png)

### AI分析过程
![AI分析](./docs/screenshots/analysis.png)

### 结果展示
![结果](./docs/screenshots/results.png)

### 移动端
![移动端](./docs/screenshots/mobile.png)

---

## 📖 文档

- [📘 快速开始](./快速开始.md)
- [📗 完整使用指南](./docs/完整使用指南.md)
- [📙 云端部署步骤](./docs/云端部署步骤.md)
- [📕 本地爬虫使用指南](./docs/本地爬虫使用指南.md)
- [📔 产品升级计划](./产品升级计划.md)
- [📓 GitHub高星项目对标](./GitHub高星项目对标.md)

---

## 🚀 路线图

### ✅ 已完成（v1.0）

- [x] 6个AI协作引擎
- [x] 简历分析
- [x] 岗位推荐
- [x] 简历优化
- [x] 面试辅导
- [x] 移动端适配
- [x] 性能优化
- [x] 自动部署

### 🔄 进行中（v1.1）

- [ ] 用户系统（注册/登录）
- [ ] 简历多版本管理
- [ ] 投递记录追踪
- [ ] 数据统计仪表板

### 📅 计划中（v2.0）

- [ ] 会员体系
- [ ] 支付接口
- [ ] AI面试官（语音对话）
- [ ] 智能投递助手
- [ ] 职业规划AI
- [ ] 社区功能

### 🌟 未来（v3.0）

- [ ] 企业端产品
- [ ] API开放平台
- [ ] 培训课程
- [ ] 猎头服务
- [ ] 国际化

---

## 🤝 贡献

欢迎贡献代码、报告问题、提出建议！

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献者

感谢所有贡献者！

<a href="https://github.com/emptyteabot/ai-job-helper/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=emptyteabot/ai-job-helper" />
</a>

---

## 📊 项目统计

![GitHub stars](https://img.shields.io/github/stars/emptyteabot/ai-job-helper?style=social)
![GitHub forks](https://img.shields.io/github/forks/emptyteabot/ai-job-helper?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/emptyteabot/ai-job-helper?style=social)

![GitHub issues](https://img.shields.io/github/issues/emptyteabot/ai-job-helper)
![GitHub pull requests](https://img.shields.io/github/issues-pr/emptyteabot/ai-job-helper)
![GitHub last commit](https://img.shields.io/github/last-commit/emptyteabot/ai-job-helper)

---

## 💰 商业化

### 免费版（永久免费）

- ✅ 每月3次AI分析
- ✅ 基础简历优化
- ✅ 查看10个推荐岗位

### 专业版（¥99/月）

- ✅ 无限次AI分析
- ✅ 高级简历优化
- ✅ 无限岗位推荐
- ✅ 自动投递（50次/月）
- ✅ AI面试辅导
- ✅ 数据分析报告

### 企业版（¥999/月）

- ✅ 专业版所有功能
- ✅ 自动投递（无限）
- ✅ 专属AI顾问
- ✅ 优先客服
- ✅ API接口
- ✅ 定制化服务

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=emptyteabot/ai-job-helper&type=Date)](https://star-history.com/#emptyteabot/ai-job-helper&Date)

---

## 📄 许可证

本项目采用 [MIT License](./LICENSE) 开源协议。

---

## 🙏 致谢

### 技术栈

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [DeepSeek](https://www.deepseek.com/) - 强大的AI模型
- [Railway](https://railway.app/) - 简单易用的云平台
- [OpenClaw](https://github.com/getcursor/openclaw) - 浏览器自动化工具

### 灵感来源

- [Resume.io](https://resume.io/) - 简历优化
- [JobSpy](https://github.com/Bunsly/JobSpy) - 岗位爬取
- [Reactive Resume](https://github.com/AmruthPillai/Reactive-Resume) - 开源简历
- [Interview Warmup](https://grow.google/certificates/interview-warmup/) - 面试练习

---

## 📞 联系我们

- **GitHub：** [emptyteabot/ai-job-helper](https://github.com/emptyteabot/ai-job-helper)
- **网站：** [https://ai-job-hunter-production-2730.up.railway.app](https://ai-job-hunter-production-2730.up.railway.app)
- **讨论：** [GitHub Discussions](https://github.com/emptyteabot/ai-job-helper/discussions)
- **问题：** [GitHub Issues](https://github.com/emptyteabot/ai-job-helper/issues)

---

## 🎉 支持我们

如果这个项目对您有帮助，请：

- ⭐ 给项目点个Star
- 🔀 Fork并贡献代码
- 📢 分享给更多人
- 💰 赞助我们（开发中）

---

<div align="center">

**让AI助力，让求职无忧** 🚀

Made with ❤️ by [emptyteabot](https://github.com/emptyteabot)

</div>
