# 🤝 贡献指南

感谢你对 AI求职助手 项目的关注！我们欢迎所有形式的贡献。

## 📋 贡献方式

### 1. 报告 Bug

如果你发现了 Bug，请：

1. 检查 [Issues](https://github.com/emptyteabot/ai-job-helper/issues) 是否已有相同问题
2. 如果没有，创建新 Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（操作系统、Python 版本等）
   - 截图或错误日志（如有）

### 2. 提出新功能

如果你有好的想法：

1. 先创建 Issue 讨论
2. 说明功能的用途和价值
3. 提供设计思路（可选）
4. 等待维护者反馈

### 3. 提交代码

#### 准备工作

```bash
# 1. Fork 项目到你的 GitHub

# 2. 克隆你的 Fork
git clone https://github.com/YOUR_USERNAME/ai-job-helper.git
cd ai-job-helper

# 3. 添加上游仓库
git remote add upstream https://github.com/emptyteabot/ai-job-helper.git

# 4. 创建新分支
git checkout -b feature/your-feature-name
```

#### 开发规范

**代码风格**

- 遵循 PEP 8 规范
- 使用有意义的变量名
- 添加必要的注释
- 保持代码简洁

**提交信息**

使用语义化提交信息：

```
feat: 添加新功能
fix: 修复 Bug
docs: 更新文档
style: 代码格式调整
refactor: 重构代码
test: 添加测试
chore: 构建/工具链更新
```

示例：
```
feat: 添加简历模板下载功能

- 支持 PDF 和 Word 格式
- 提供 3 种模板选择
- 添加预览功能
```

**测试**

```bash
# 运行测试
pytest

# 检查覆盖率
pytest --cov=app tests/
```

#### 提交 Pull Request

```bash
# 1. 确保代码最新
git fetch upstream
git rebase upstream/main

# 2. 推送到你的 Fork
git push origin feature/your-feature-name

# 3. 在 GitHub 上创建 Pull Request
```

**PR 描述模板**

```markdown
## 变更说明
简要描述这个 PR 做了什么

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化

## 测试
- [ ] 已添加测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 截图（如有）
添加截图展示变更效果

## 相关 Issue
Closes #issue_number
```

### 4. 改进文档

文档同样重要！你可以：

- 修正错别字
- 改进说明
- 添加示例
- 翻译文档

## 🎯 开发指南

### 项目结构

```
ai-job-helper/
├── app/                    # 核心应用
│   ├── core/              # 核心功能
│   │   ├── multi_ai_debate.py      # 6 AI 协作引擎
│   │   ├── fast_ai_engine.py       # 快速 AI 引擎
│   │   └── market_driven_engine.py # 市场驱动引擎
│   └── services/          # 业务服务
│       ├── auto_apply/    # 自动投递模块
│       │   ├── boss_applier.py     # Boss直聘
│       │   ├── zhilian_applier.py  # 智联招聘
│       │   └── linkedin_applier.py # LinkedIn
│       ├── resume_analyzer.py      # 简历分析
│       └── real_job_service.py     # 真实岗位服务
├── pages/                 # Streamlit 页面
│   ├── 1_📄_简历分析.py
│   └── 2_🚀_自动投递.py
├── tests/                 # 测试文件
├── docs/                  # 文档
├── streamlit_app.py       # Streamlit 主应用
├── web_app.py            # FastAPI 主应用
└── requirements.txt       # 依赖包
```

### 本地开发

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

#### 3. 启动开发服务器

**Streamlit 版本**
```bash
streamlit run streamlit_app.py
```

**FastAPI 版本**
```bash
python web_app.py
```

#### 4. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_resume_analyzer.py

# 查看覆盖率
pytest --cov=app tests/
```

### 添加新功能

#### 示例：添加新的自动投递平台

1. **创建新的 Applier 类**

```python
# app/services/auto_apply/new_platform_applier.py

from .base_applier import BaseApplier

class NewPlatformApplier(BaseApplier):
    def __init__(self, config):
        super().__init__(config)
        self.platform_name = "新平台"

    async def login(self):
        """登录逻辑"""
        pass

    async def search_jobs(self, keywords, location):
        """搜索岗位"""
        pass

    async def apply_job(self, job_id):
        """投递简历"""
        pass
```

2. **添加测试**

```python
# tests/test_new_platform_applier.py

import pytest
from app.services.auto_apply.new_platform_applier import NewPlatformApplier

def test_login():
    applier = NewPlatformApplier(config)
    result = await applier.login()
    assert result is True
```

3. **更新文档**

在 README.md 中添加新平台说明

4. **提交 PR**

## 🐛 调试技巧

### 启用调试日志

```python
# 在 .env 中设置
LOG_LEVEL=DEBUG
```

### 使用 Python 调试器

```python
import pdb; pdb.set_trace()
```

### Streamlit 调试

```python
import streamlit as st
st.write("Debug info:", variable)
```

## 📝 代码审查清单

提交 PR 前，请确认：

- [ ] 代码遵循项目规范
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 添加了测试用例
- [ ] 所有测试通过
- [ ] 没有引入新的警告
- [ ] 提交信息清晰明确

## 🎨 UI/UX 贡献

如果你擅长设计：

- 改进界面布局
- 优化用户体验
- 设计新的图标
- 提供配色方案

请在 Issue 中分享你的设计稿或原型。

## 📚 文档贡献

文档位于：
- `README.md` - 项目主文档
- `docs/` - 详细文档
- `DEPLOYMENT_GUIDE.md` - 部署指南
- 代码注释

## 🌍 国际化

我们欢迎翻译贡献：

1. 创建新的语言文件
2. 翻译界面文本
3. 更新文档

## 💬 社区

- GitHub Discussions: 讨论功能和想法
- GitHub Issues: 报告 Bug 和提出功能请求
- Pull Requests: 提交代码贡献

## 📄 许可证

贡献的代码将采用 MIT 许可证。

## 🙏 致谢

感谢所有贡献者！你们的贡献让这个项目变得更好。

---

**有问题？** 随时在 Issues 中提问，我们会尽快回复！

💼 祝你贡献愉快！
