# 🚀 Streamlit Cloud 部署指南

## 📋 前置准备

1. ✅ GitHub 账号
2. ✅ Streamlit Cloud 账号（免费）
3. ✅ 代码已推送到 GitHub

## 🔗 部署步骤

### 1. 访问 Streamlit Cloud

打开浏览器访问：
```
https://streamlit.io/cloud
```

### 2. 登录账号

- 点击 "Sign in"
- 使用 GitHub 账号登录
- 授权 Streamlit 访问你的仓库

### 3. 创建新应用

1. 点击 "New app" 按钮
2. 选择仓库：`emptyteabot/ai-job-helper`
3. 选择分支：`main`
4. 选择主文件：`streamlit_app.py`
5. 点击 "Deploy!"

### 4. 等待部署

- 部署通常需要 2-5 分钟
- 可以查看实时日志
- 部署成功后会自动打开应用

### 5. 获取应用链接

部署成功后，你会得到一个链接：
```
https://your-app-name.streamlit.app
```

## ⚙️ 高级配置

### 环境变量

如果需要配置环境变量：

1. 点击应用右上角的 "⋮" 菜单
2. 选择 "Settings"
3. 点击 "Secrets"
4. 添加环境变量（TOML 格式）

示例：
```toml
# .streamlit/secrets.toml
API_KEY = "your-api-key"
API_BASE_URL = "https://your-api.com"
```

### 自定义域名

1. 在 Settings 中选择 "General"
2. 找到 "Custom subdomain"
3. 输入你想要的子域名
4. 保存设置

### 资源限制

免费版限制：
- CPU: 1 core
- RAM: 1 GB
- 存储: 无限制
- 带宽: 无限制
- 应用数量: 无限制

## 🔄 更新应用

### 自动更新

Streamlit Cloud 会自动监听 GitHub 仓库的变化：

1. 推送代码到 GitHub
   ```bash
   git add .
   git commit -m "更新功能"
   git push
   ```

2. Streamlit Cloud 自动检测并重新部署
3. 等待 1-2 分钟即可看到更新

### 手动重启

如果需要手动重启：

1. 点击应用右上角的 "⋮" 菜单
2. 选择 "Reboot app"
3. 等待应用重启

## 📊 监控和日志

### 查看日志

1. 点击应用右下角的 "Manage app"
2. 选择 "Logs" 标签
3. 查看实时日志输出

### 查看指标

1. 在 "Manage app" 页面
2. 选择 "Analytics" 标签
3. 查看访问量、性能等指标

## ⚠️ 常见问题

### 1. 部署失败

**原因**：依赖安装失败

**解决**：
- 检查 `requirements.txt` 格式
- 确保所有依赖版本兼容
- 查看部署日志找到具体错误

### 2. 应用启动慢

**原因**：首次启动需要安装依赖

**解决**：
- 等待 2-5 分钟
- 后续访问会更快
- 考虑优化依赖数量

### 3. 内存不足

**原因**：免费版只有 1GB RAM

**解决**：
- 优化代码减少内存使用
- 使用缓存机制
- 升级到付费版

### 4. API 连接失败

**原因**：后端 API 不可用

**解决**：
- 检查 API 地址是否正确
- 确认后端服务正常运行
- 检查网络连接

### 5. 文件上传失败

**原因**：文件大小超限

**解决**：
- 默认限制 200MB
- 在 `.streamlit/config.toml` 中调整：
  ```toml
  [server]
  maxUploadSize = 500
  ```

## 🔒 安全建议

1. **不要在代码中硬编码密钥**
   - 使用 Streamlit Secrets
   - 使用环境变量

2. **限制访问**
   - 在 Settings 中设置密码保护
   - 使用 GitHub 私有仓库

3. **定期更新依赖**
   - 检查安全漏洞
   - 更新到最新版本

## 📱 分享应用

### 公开分享

直接分享应用链接：
```
https://your-app-name.streamlit.app
```

### 嵌入网页

使用 iframe 嵌入：
```html
<iframe
  src="https://your-app-name.streamlit.app/?embed=true"
  height="600"
  width="100%"
></iframe>
```

### 社交媒体

Streamlit 会自动生成预览卡片，适合分享到：
- Twitter
- LinkedIn
- Facebook
- 微信

## 💰 升级到付费版

如果需要更多资源：

1. 访问 https://streamlit.io/cloud
2. 点击 "Upgrade"
3. 选择合适的套餐

付费版优势：
- 更多 CPU 和 RAM
- 更快的启动速度
- 优先技术支持
- 自定义域名
- 密码保护

## 📞 获取帮助

- 官方文档：https://docs.streamlit.io/
- 社区论坛：https://discuss.streamlit.io/
- GitHub Issues：https://github.com/streamlit/streamlit/issues

---

🎉 祝你部署顺利！
