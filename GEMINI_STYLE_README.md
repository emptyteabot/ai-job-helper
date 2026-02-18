# 🚀 Gemini Style Streamlit 应用启动指南

## ✨ 特性

### 🎨 Material Design 风格
- **Google 蓝 + 紫色渐变背景**：动态旋转的多彩渐变
- **Material Design 阴影**：4 级阴影系统
- **圆角胶囊按钮**：流畅的悬停动画
- **品牌点脉冲动画**：Google 风格的呼吸效果
- **Google Sans 字体**：专业的 Google 字体

### 🎭 酷炫动画
- ✅ 淡入/滑入动画（fadeInUp, slideInLeft）
- ✅ 旋转背景渐变（15秒循环）
- ✅ 脉冲品牌点动画
- ✅ 步骤指示器缩放动画
- ✅ 卡片悬停提升效果
- ✅ 按钮悬停阴影变化

### 📦 完整功能
- ✅ 简历分析（上传/粘贴）
- ✅ AI 智能分析
- ✅ 实时职位推荐
- ✅ 自动投递（开发中）
- ✅ 文档中心
- ✅ 帮助中心

## 🚀 启动步骤

### 1. 启动后端 API
```bash
cd "C:\Users\陈盈桦\Desktop\Desktop_整理_2026-02-09_172732\Folders\自动投简历"
python app.py
```

### 2. 启动 Streamlit 应用
```bash
streamlit run streamlit_app.py
```

### 3. 访问应用
浏览器自动打开：http://localhost:8501

## 📁 文件说明

- `streamlit_app.py` - 主应用（已替换为 Gemini 风格）
- `streamlit_app_gemini.py` - Gemini 风格版本（备份）
- `app.py` - FastAPI 后端服务
- `static/app.html` - 原始 HTML 设计参考

## 🎨 设计亮点

### Hero 区域
- 蓝紫渐变背景
- 旋转的光晕效果
- 脉冲动画徽章
- 滑入动画标题

### 步骤指示器
- 4 步流程可视化
- 动态状态切换（pending/active/done）
- 缩放动画效果
- Google 配色方案

### 职位卡片
- 左侧蓝色边框
- 悬停滑动效果
- Material Design 阴影
- 响应式布局

### 按钮样式
- 蓝紫渐变背景
- 圆角胶囊形状
- 悬停提升动画
- 阴影层级变化

## 🔧 技术栈

- **前端框架**：Streamlit
- **样式系统**：Material Design + Google 风格
- **字体**：Google Sans, Roboto
- **动画**：CSS3 Keyframes
- **后端 API**：FastAPI
- **AI 模型**：Gemini / OpenAI

## 📝 使用流程

1. **上传简历**：支持 PDF/DOCX/TXT/图片
2. **AI 分析**：点击「开始分析」按钮
3. **查看结果**：职业分析、职位推荐、优化简历等
4. **实时职位**：自动匹配并显示职位卡片
5. **下载报告**：导出完整分析报告

## 🎯 下一步

- [ ] 完善自动投递功能
- [ ] 添加更多动画效果
- [ ] 优化移动端体验
- [ ] 集成更多 AI 模型
- [ ] 添加用户认证系统

## 💡 提示

- 确保后端 API 运行在 `http://localhost:8000`
- 首次运行可能需要安装依赖：`pip install -r requirements.txt`
- 如遇到问题，检查控制台日志

---

**Powered by Gemini & Material Design** ✨
