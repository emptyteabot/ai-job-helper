# Streamlit 配置说明

## 环境变量配置

在 Streamlit Cloud 上需要配置以下环境变量：

### 必需的 API Keys

```bash
# DeepSeek API（用于 AI 分析）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 或者使用 OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://oneapi.gemiaude.com/v1
```

### 可选配置

```bash
# 日志级别
APP_LOG_LEVEL=INFO

# 数据库（本地使用 SQLite，云端可选）
DATABASE_URL=sqlite:///./data/jobs.db
```

## Streamlit Cloud 配置步骤

1. **访问 Streamlit Cloud**
   - https://share.streamlit.io/

2. **进入应用设置**
   - 点击你的应用
   - 点击右上角 "Settings"

3. **添加 Secrets**
   - 点击 "Secrets"
   - 添加以下内容：

```toml
# .streamlit/secrets.toml
DEEPSEEK_API_KEY = "your_key_here"
OPENAI_API_KEY = "your_key_here"
OPENAI_BASE_URL = "https://oneapi.gemiaude.com/v1"
```

4. **保存并重启**
   - 点击 "Save"
   - 应用会自动重启

## 本地测试

创建 `.streamlit/secrets.toml` 文件：

```bash
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
DEEPSEEK_API_KEY = "your_key_here"
OPENAI_API_KEY = "your_key_here"
OPENAI_BASE_URL = "https://oneapi.gemiaude.com/v1"
EOF
```

然后运行：

```bash
streamlit run streamlit_app.py
```

## 功能限制

### Streamlit Cloud 支持：
- ✅ 简历分析（AI 功能）
- ✅ 文本输入
- ✅ 文件上传（需要解析库）

### Streamlit Cloud 不支持：
- ❌ 浏览器自动化（Playwright/Selenium）
- ❌ 自动投递功能

### 解决方案：

**方案 1：本地运行自动投递**
```bash
python web_app.py
# 访问 http://localhost:8000
```

**方案 2：使用 Railway 部署后端**
- 后端（web_app.py）部署到 Railway
- 前端（streamlit_app.py）部署到 Streamlit Cloud
- 前端调用后端 API

**方案 3：全部本地运行**
```bash
streamlit run streamlit_app.py
```

## 推荐架构

```
┌─────────────────────┐
│  Streamlit Cloud    │  ← 简历分析（AI 功能）
│  (前端 UI)          │
└─────────────────────┘
          │
          │ API 调用
          ↓
┌─────────────────────┐
│  Railway/本地       │  ← 自动投递（浏览器自动化）
│  (后端服务)         │
└─────────────────────┘
```

## 当前状态

- ✅ Streamlit 应用已更新
- ✅ 简历分析功能集成
- ⚠️ 需要配置 API Keys
- ⚠️ 自动投递需要本地运行或 Railway 后端

## 下一步

1. **配置 Streamlit Cloud Secrets**
   - 添加 API Keys

2. **推送代码到 GitHub**
   ```bash
   git add .
   git commit -m "完整集成简历分析功能到 Streamlit"
   git push origin main
   ```

3. **Streamlit Cloud 自动部署**
   - 等待 2-3 分钟

4. **测试功能**
   - 访问：https://ai-job-apper-ibpzap2nnajzrnu8mkthuv.streamlit.app
   - 测试简历分析
