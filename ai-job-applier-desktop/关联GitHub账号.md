# 🔗 关联 GitHub 账号到 Streamlit Cloud

## 问题
- GitHub 账号：`emptyteabot`
- Streamlit Cloud 登录：`13398580812@163.com`
- 两个账号没有关联，导致无权限访问

## 解决方案

### 方式 1：在 Streamlit Cloud 中关联 GitHub（推荐）

1. 访问：https://share.streamlit.io/
2. 点击右上角头像 → **Settings**
3. 找到 **"Connected accounts"** 或 **"Source control"**
4. 点击 **"Connect GitHub"** 或 **"Link GitHub account"**
5. 选择 **emptyteabot** 账号授权
6. 授权完成后，刷新页面

### 方式 2：重新登录 Streamlit Cloud

1. 访问：https://share.streamlit.io/
2. 点击右上角 → **Sign out**
3. 重新登录，选择 **"Sign in with GitHub"**
4. 使用 **emptyteabot** 账号登录
5. 授权 Streamlit Cloud 访问你的仓库

### 方式 3：使用 GitHub 直接部署

1. 访问你的仓库：https://github.com/emptyteabot/ai-job-helper
2. 在仓库根目录创建 `.streamlit/config.toml` 文件
3. 点击仓库页面的 **"Deploy to Streamlit"** 按钮（如果有）
4. 或者从 Streamlit Cloud 选择 GitHub 登录

## 推荐步骤

### 1. 退出当前账号
访问：https://share.streamlit.io/
点击右上角 → **Sign out**

### 2. 使用 GitHub 登录
点击 **"Sign in with GitHub"**
使用 **emptyteabot** 账号登录

### 3. 授权访问
授权 Streamlit Cloud 访问你的 GitHub 仓库

### 4. 创建新应用
- Repository: `emptyteabot/ai-job-helper`
- Branch: `main`
- Main file path: `streamlit_app.py`

### 5. 部署
点击 **"Deploy"**，等待 2-3 分钟

## 验证

部署成功后，访问新的 URL，确认：
- ✅ 没有假验证码提示
- ✅ Gemini 渐变背景
- ✅ 4个Tab：简历分析、自动投递、文档中心、帮助中心

---

**现在去 Streamlit Cloud 退出并用 GitHub 账号重新登录！** 🚀

