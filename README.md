# 🚀 AI求职助手（本机 MVP + 云端部署）

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/你的用户名/ai-job-helper)

## 文档

- 最新文档索引：`docs/README.md`

## 功能特点（当前代码已实现）

- 🤖 6个AI协作引擎
- 🎯 市场驱动架构
- 🔎 本机实时抓岗位链接（OpenClaw + Boss，手动投递）
- 📊 本地岗位数据兜底（无 API Key 也能跑）
- 🌐 24小时在线访问

## 快速部署（云端 24h）

### 推荐：Zeabur / Railway / Render

见 `docs/deploy/云端部署指南.md`。

### 方法2: 手动部署

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/ai-job-helper.git
cd ai-job-helper

# 2. 安装Vercel CLI
npm i -g vercel

# 3. 部署
vercel --prod
```

## 本地运行（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
# 创建 .env 文件，添加：
DEEPSEEK_API_KEY=your_api_key_here

# 3. 启动服务
python web_app.py

# 4. 访问
http://localhost:8000/app
```

## 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| DEEPSEEK_API_KEY | DeepSeek API密钥 | 是 |
| PORT | 端口号 | 否（默认8000） |

## 技术栈

- **前端**: HTML5 + CSS3 + JavaScript
- **后端**: FastAPI + Python
- **AI**: DeepSeek + AsyncOpenAI
- **部署**: Vercel + GitHub

## 备注

- OpenClaw 抓取 Boss 链接只适用于本机（依赖你的浏览器登录态），不适合云端共享。

## 许可证

MIT License

## 联系方式

- GitHub: [项目地址]
- Email: contact@ai-job-helper.com

