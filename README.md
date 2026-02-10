# 🚀 AI求职助手（本机 MVP + 云端部署）

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/你的用户名/ai-job-helper)

> **一句话总结：** 用多AI协作+市场驱动架构，帮求职者精准匹配岗位的AI助手

## ✨ 核心亮点

### 🎯 技术创新
- **6个AI协作引擎** - 职业规划师、招聘专家、简历优化师等多角色辩论优化
- **市场驱动架构** - 从"简历中心"转向"真实招聘市场"为中心
- **真实岗位抓取** - OpenClaw浏览器自动化，抓取Boss直聘真实岗位链接
- **完整技术栈** - FastAPI + DeepSeek API + WebSocket实时进度

### 💼 产品功能
- ✅ 支持PDF/Word/TXT/图片OCR上传
- ✅ 实时市场匹配度分析
- ✅ 简历针对性优化
- ✅ 面试辅导和模拟
- ✅ 真实岗位链接（可直接投递）
- ✅ 一键部署（Railway/Render/本地）

## 🚀 快速开始（5分钟）

### 方式一：一键安装（推荐）

```bash
# Windows用户：双击运行
一键安装.bat

# 然后双击运行
启动网站.bat
```

### 方式二：手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
copy env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 启动服务
python web_app.py

# 4. 访问网站
# http://localhost:8000/app
```

## 📖 详细文档

- 📘 **[完整使用指南](docs/完整使用指南.md)** - 从0到1的详细教程
- 🔧 **[OpenClaw配置](docs/howto/OPENCLAW_BOSS_MVP.md)** - 真实岗位抓取配置
- 🌐 **[云端部署指南](docs/deploy/云端部署指南.md)** - Railway/Render/Vercel部署
- 🏗️ **[架构说明](docs/architecture/市场驱动架构说明.md)** - 技术架构详解

## 🎯 使用场景

### 场景1：本机使用（推荐）
- ✅ AI分析简历
- ✅ OpenClaw抓取Boss直聘真实岗位
- ✅ 一键跳转投递

**适合：** 个人求职者，需要真实岗位数据

### 场景2：云端部署
- ✅ 24小时在线访问
- ✅ AI分析简历
- ⚠️ 使用本地模拟数据（OpenClaw不适合云端）

**适合：** 演示、分享、多人使用

## 🔧 环境变量配置

创建 `.env` 文件：

```env
# 必填：DeepSeek API密钥
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 可选：岗位数据源
# - openclaw: 抓取Boss直聘真实岗位（推荐，需要本机浏览器）
# - local: 使用本地模拟数据（无需配置，适合演示）
# - jooble: 使用Jooble API（需要JOOBLE_API_KEY）
JOB_DATA_PROVIDER=openclaw

# 可选：服务端口
PORT=8000
```

## 🌟 OpenClaw真实岗位抓取

### 什么是OpenClaw？
OpenClaw是一个浏览器自动化工具，可以：
- 控制您已登录的Chrome浏览器
- 自动打开Boss直聘搜索页
- 抓取真实岗位详情链接
- 让您一键跳转投递

### 配置步骤（只需一次）

```bash
# 1. 安装OpenClaw
pip install openclaw

# 2. 安装Chrome扩展
openclaw browser install-extension

# 3. 启动浏览器
openclaw browser start

# 4. 在Chrome中打开Boss直聘并登录
# https://www.zhipin.com

# 5. 点击OpenClaw扩展图标，点击"Attach"
```

### 验证状态

访问 `http://localhost:8000/api/health` 查看OpenClaw状态：

```json
{
  "openclaw": {
    "available": true,
    "status": "ok",
    "message": "✅ OpenClaw已就绪，可以抓取Boss直聘岗位"
  }
}
```

## 📊 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     用户界面 (Web)                        │
│              FastAPI + WebSocket实时进度                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  多AI协作引擎                             │
│  👔职业规划师 → 🔍招聘专家 → ✍️简历优化师                 │
│  → ✅质量检查官 → 🎓面试教练 → 🎭模拟面试官               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  真实岗位数据源                           │
│  OpenClaw → Boss直聘/猎聘/智联/前程无忧                   │
│  Jooble API → 国际岗位                                    │
│  本地数据库 → 1000+模拟岗位（演示用）                      │
└─────────────────────────────────────────────────────────┘
```

## 🎓 核心功能演示

### 1. 上传简历
支持多种格式：
- 📄 PDF文件
- 📝 Word文档（.docx, .doc）
- 📋 纯文本（.txt）
- 🖼️ 图片（.jpg, .png）- 自动OCR识别

### 2. AI协作分析
6个AI角色依次工作（1-2分钟）：
1. **职业规划师** - 分析优势和定位
2. **招聘专家** - 搜索匹配岗位
3. **简历优化师** - 针对性改写
4. **质量检查官** - 审核改进
5. **面试教练** - 面试辅导
6. **模拟面试官** - 模拟问答

### 3. 真实岗位搜索
- 自动根据简历生成搜索关键词
- OpenClaw抓取Boss直聘岗位链接
- 展示岗位列表（标题、公司、薪资、地点）
- 一键跳转到Boss直聘投递

### 4. 投递记录
- 自动记录投递历史
- 跟踪投递状态
- 统计投递数据

## 🌐 云端部署

### Railway（推荐）

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

```bash
# 一键部署
railway up
```

### Render

```bash
# 连接GitHub仓库，自动部署
```

### Vercel

```bash
vercel --prod
```

**注意：** 云端部署不支持OpenClaw，建议使用 `JOB_DATA_PROVIDER=local`

## 📈 项目数据

- **总岗位数据库**: 1000+ 真实公司岗位（本地模式）
- **支持平台**: Boss直聘、猎聘、智联招聘、前程无忧
- **AI模型**: DeepSeek-V3（高性能、低成本）
- **响应时间**: AI分析 1-2分钟，岗位搜索 10-30秒

## ❓ 常见问题

### Q: 为什么选择OpenClaw而不是API？
**A:** Boss直聘等国内招聘网站不提供公开API，OpenClaw使用您自己的浏览器和登录态，合法合规地获取真实岗位链接。

### Q: OpenClaw安全吗？
**A:** 完全安全。OpenClaw运行在您的本机，使用您自己的浏览器，不会上传任何账号信息。

### Q: 不使用OpenClaw可以吗？
**A:** 可以！设置 `JOB_DATA_PROVIDER=local` 使用本地模拟数据，适合演示和测试。

### Q: 支持哪些招聘网站？
**A:** 当前支持Boss直聘（推荐）、猎聘、智联招聘、前程无忧。建议只使用Boss直聘，最稳定。

## 🔧 故障排查

### "OpenClaw未安装"
```bash
pip install openclaw
```

### "OpenClaw浏览器未连接标签页"
1. 运行 `openclaw browser start`
2. 在Chrome中打开Boss直聘
3. 点击OpenClaw扩展图标并Attach

### "DeepSeek API调用失败"
1. 检查 `.env` 中的 `DEEPSEEK_API_KEY`
2. 访问 https://platform.deepseek.com 检查API额度

**更多问题？** 查看 [完整使用指南](docs/完整使用指南.md)

## 🛣️ 路线图

### ✅ 已完成
- [x] 多AI协作引擎
- [x] 市场驱动架构
- [x] OpenClaw集成
- [x] PDF/Word/图片上传
- [x] WebSocket实时进度
- [x] 一键部署

### 🚧 进行中
- [ ] 用户系统和登录
- [ ] 投递数据分析
- [ ] 薪资趋势分析
- [ ] 移动端适配

### 📅 计划中
- [ ] 多平台同步投递
- [ ] AI面试模拟（语音）
- [ ] 职业发展规划
- [ ] 企业背景调查

## 💰 商业模式（规划中）

### 免费版
- ✅ 基础AI分析
- ✅ 本地模拟数据
- ⚠️ 每日3次分析

### 专业版（¥99/月）
- ✅ 无限次AI分析
- ✅ OpenClaw真实岗位
- ✅ 投递数据分析
- ✅ 优先客服支持

### 企业版（定制）
- ✅ 批量简历分析
- ✅ 团队协作
- ✅ 私有化部署
- ✅ 定制开发

## 🤝 贡献指南

欢迎贡献代码、报告问题、提出建议！

```bash
# 1. Fork项目
# 2. 创建分支
git checkout -b feature/your-feature

# 3. 提交代码
git commit -m "Add your feature"

# 4. 推送分支
git push origin feature/your-feature

# 5. 创建Pull Request
```

## 📄 许可证

MIT License - 自由使用和修改

## 📞 联系方式

- 📧 Email: contact@ai-job-helper.com
- 💬 微信: [加入交流群]
- 🐛 Issues: [GitHub Issues](https://github.com/你的用户名/ai-job-helper/issues)

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**

**祝您求职顺利！🎉**
