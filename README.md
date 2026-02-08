# 🚀 AI求职助手

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/你的用户名/ai-job-helper)

## 在线访问

🌐 **24小时在线**: https://你的域名.vercel.app

## 功能特点

- 🤖 6个AI协作引擎
- 🎯 市场驱动架构
- 📊 真实岗位数据（1000+）
- ⚡ 5秒完成分析
- 🌐 24小时在线访问

## 快速部署

### 方法1: Vercel一键部署（推荐）

1. 点击上方 "Deploy with Vercel" 按钮
2. 使用GitHub登录
3. 创建新仓库
4. 添加环境变量 `DEEPSEEK_API_KEY`
5. 点击Deploy
6. 等待部署完成（约2分钟）

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

## 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
# 创建 .env 文件，添加：
DEEPSEEK_API_KEY=your_api_key_here

# 3. 启动服务
python web_app.py

# 4. 访问
http://localhost:8000
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

## 更新日志

### v3.0.0 (2024-02-08)
- ✅ 市场驱动架构
- ✅ 真实岗位数据
- ✅ 并行处理（5秒完成）
- ✅ 自动部署脚本

### v2.0.0 (2024-02-08)
- ✅ WebSocket实时进度
- ✅ 技能图谱系统
- ✅ Agent协调器

## 许可证

MIT License

## 联系方式

- GitHub: [项目地址]
- Email: contact@ai-job-helper.com

