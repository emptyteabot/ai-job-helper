# 🎓 AI求职助手 - Streamlit 版本

专为大学生实习求职打造的智能助手

## 🌟 功能特点

### 📄 AI 简历分析
- **6 大 AI 协作深度分析**
  - 🎯 职业分析
  - 💼 岗位推荐
  - ✍️ 简历优化
  - 📚 面试准备
  - 🎤 模拟面试
  - 📈 技能差距分析

### 🚀 自动投递
- **三大平台同步投递**
  - 🟦 Boss直聘
  - 🟨 智联招聘
  - 🟦 LinkedIn
- **智能功能**
  - 多平台并行投递
  - 实时进度追踪
  - 投递数据统计
  - 黑名单管理

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run streamlit_app.py
```

### 3. 访问应用

浏览器自动打开 `http://localhost:8501`

## 📁 项目结构

```
.
├── streamlit_app.py          # 主应用文件
├── pages/
│   ├── 1_📄_简历分析.py      # 简历分析页面
│   └── 2_🚀_自动投递.py      # 自动投递页面
├── .streamlit/
│   └── config.toml           # Streamlit 配置
├── app/                      # 后端服务
│   ├── core/                 # 核心功能
│   └── services/             # 业务服务
│       └── auto_apply/       # 自动投递模块
│           ├── boss_applier.py      # Boss直聘
│           ├── zhilian_applier.py   # 智联招聘
│           └── linkedin_applier.py  # LinkedIn
└── requirements.txt          # 依赖包
```

## 🔧 配置说明

### 后端 API

默认使用 Railway 部署的后端：
```
https://ai-job-hunter-production-2730.up.railway.app
```

如需修改，请编辑：
- `pages/1_📄_简历分析.py` 第 88 行
- `pages/2_🚀_自动投递.py` 第 21 行

### Streamlit 配置

配置文件：`.streamlit/config.toml`

可自定义：
- 主题颜色
- 服务器端口
- CORS 设置

## 📝 使用说明

### 简历分析

1. 点击左侧导航 "📄 简历分析"
2. 上传简历文件或粘贴文本
3. 点击 "🚀 开始分析"
4. 查看 6 大维度分析结果
5. 下载分析报告

### 自动投递

1. 点击左侧导航 "🚀 自动投递"
2. 选择投递平台
3. 配置搜索关键词和地点
4. 填写平台账号信息
5. 点击 "▶️ 开始投递"
6. 实时查看投递进度

## ⚠️ 注意事项

1. **首次使用**
   - 建议先测试少量投递
   - 确保账号信息正确

2. **投递建议**
   - 工作日 9:00-17:00 投递效果最佳
   - 设置 5-10 秒投递间隔
   - 定期更新黑名单

3. **安全提示**
   - 遵守各平台使用规则
   - 避免频繁操作被封号
   - 定期检查投递效果

## 🛠️ 技术栈

- **前端**: Streamlit
- **后端**: FastAPI
- **AI**: OpenAI API
- **自动化**:
  - Playwright Stealth (Boss直聘)
  - DrissionPage (智联招聘)
  - Selenium (LinkedIn)

## 📊 部署

### Streamlit Cloud

1. Fork 本仓库
2. 访问 [Streamlit Cloud](https://streamlit.io/cloud)
3. 连接 GitHub 仓库
4. 选择 `streamlit_app.py`
5. 点击 Deploy

### 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run streamlit_app.py --server.port 8501
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 💬 联系方式

如有问题，请提交 Issue 或联系开发者。

---

💼 祝你求职顺利！
