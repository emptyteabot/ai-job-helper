# 部署到 Hugging Face Spaces

## 步骤

1. 访问 https://huggingface.co/spaces
2. 点击 "Create new Space"
3. 选择 "Streamlit" 作为 SDK
4. 上传你的代码或连接 GitHub
5. 等待部署完成

## 优势

- ✅ 完全免费
- ✅ 自动 HTTPS
- ✅ 免费域名：your-app.hf.space
- ✅ 支持 Streamlit
- ✅ 自动部署

## 配置文件

创建 `requirements.txt`:
```
streamlit
requests
```

创建 `README.md`:
```
---
title: AI求职助手
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: 1.28.0
app_file: streamlit_app.py
pinned: false
---
```

## 部署

1. 将 `自动投简历/streamlit_app.py` 重命名为 `app.py`
2. 上传到 Hugging Face Space
3. 等待部署完成
4. 访问 your-app.hf.space

