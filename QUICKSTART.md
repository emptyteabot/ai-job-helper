# 🚀 快速开始指南

5 分钟快速上手 AI求职助手！

## 📋 前置要求

- Python 3.8 或更高版本
- Git（可选）

## 🎯 方式一：在线体验（最快）

直接访问在线版本，无需安装：

```
https://ai-job-hunter-production-2730.up.railway.app
```

1. 打开网页
2. 上传简历或粘贴文本
3. 点击"开始AI分析"
4. 查看分析结果

## 💻 方式二：本地运行（推荐）

### Windows 用户

```bash
# 1. 下载项目
git clone https://github.com/emptyteabot/ai-job-helper.git
cd ai-job-helper

# 2. 双击运行
start.bat
```

就这么简单！浏览器会自动打开应用。

### Mac/Linux 用户

```bash
# 1. 下载项目
git clone https://github.com/emptyteabot/ai-job-helper.git
cd ai-job-helper

# 2. 运行启动脚本
chmod +x start.sh
./start.sh
```

## 🎨 使用 Streamlit 版本

Streamlit 版本界面更现代，操作更简单：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run streamlit_app.py
```

访问 `http://localhost:8501`

## 🔧 配置 API Key（可选）

如果要使用完整功能，需要配置 DeepSeek API Key：

```bash
# 1. 复制配置文件
cp .env.example .env

# 2. 编辑 .env 文件
# 将 your_deepseek_api_key_here 替换为你的真实 API Key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# 3. 重启应用
```

### 获取 API Key

1. 访问 [DeepSeek](https://platform.deepseek.com/)
2. 注册账号
3. 在控制台创建 API Key
4. 复制到 .env 文件

## 📱 功能使用

### 1. 简历分析

**步骤**：
1. 点击左侧"📄 简历分析"
2. 上传简历文件或粘贴文本
3. 点击"🚀 开始分析"
4. 等待 30-60 秒
5. 查看 6 大维度分析结果

**支持格式**：
- PDF
- Word (doc, docx)
- 图片 (png, jpg)
- 纯文本

### 2. 自动投递

**步骤**：
1. 点击左侧"🚀 自动投递"
2. 选择投递平台（Boss直聘/智联招聘/LinkedIn）
3. 填写搜索关键词和地点
4. 配置平台账号信息
5. 点击"▶️ 开始投递"
6. 实时查看投递进度

**注意事项**：
- 首次使用建议少量测试
- 设置合理的投递间隔（5-10秒）
- 及时更新黑名单

## 🎓 大学生专属功能

### 默认配置

系统已为大学生实习求职优化：

- **关键词**：实习生、应届生、校招、管培生
- **地点**：北京、上海、深圳、杭州、成都
- **学历**：本科、硕士
- **经验**：应届生、1年以下

### 简历模板

系统会根据你的专业推荐合适的简历模板。

## ⚠️ 常见问题

### 1. 启动失败

**问题**：运行 start.bat 报错

**解决**：
```bash
# 检查 Python 版本
python --version

# 应该显示 Python 3.8 或更高

# 手动安装依赖
pip install -r requirements.txt
```

### 2. 分析超时

**问题**：简历分析一直转圈

**解决**：
- 检查网络连接
- 确认 API Key 配置正确
- 简历文件不要太大（< 10MB）

### 3. 投递失败

**问题**：自动投递显示失败

**解决**：
- 检查账号密码是否正确
- 确认平台没有验证码
- 降低投递速度（增加间隔时间）

### 4. 端口被占用

**问题**：提示端口 8501 已被使用

**解决**：
```bash
# 使用其他端口
streamlit run streamlit_app.py --server.port 8502
```

## 📊 性能优化

### 加快分析速度

1. 使用文本输入而非文件上传
2. 简历内容精简到 1-2 页
3. 避免使用大图片

### 提高投递成功率

1. 完善简历信息
2. 选择匹配度高的岗位
3. 避开高峰时段（晚上 8-10 点）
4. 定期更新简历

## 🎯 下一步

- 📖 阅读 [完整文档](./README.md)
- 🚀 查看 [部署指南](./DEPLOYMENT_GUIDE.md)
- 🤝 参与 [贡献](./CONTRIBUTING.md)
- 💬 加入 [讨论](https://github.com/emptyteabot/ai-job-helper/discussions)

## 💡 使用技巧

### 简历优化

1. 先进行简历分析
2. 根据建议修改简历
3. 重新分析验证效果
4. 迭代优化直到满意

### 批量投递

1. 准备好优化后的简历
2. 设置合理的关键词
3. 添加不合适的公司到黑名单
4. 分批次投递（每次 20-30 个）
5. 定期查看反馈

### 面试准备

1. 查看"面试准备"分析结果
2. 针对性准备常见问题
3. 使用"模拟面试"功能练习
4. 记录面试经验

## 📞 获取帮助

遇到问题？

1. 查看 [常见问题](./README.md#常见问题)
2. 搜索 [Issues](https://github.com/emptyteabot/ai-job-helper/issues)
3. 创建新 Issue 提问
4. 加入社区讨论

---

💼 祝你求职顺利！

**开始使用** → [在线体验](https://ai-job-hunter-production-2730.up.railway.app) | [本地运行](#方式二本地运行推荐)
