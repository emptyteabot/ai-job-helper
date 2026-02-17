# 自动投递使用指南

## 📖 功能介绍

自动投递功能整合了 GitHub 高星开源项目 [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn)（1544⭐），实现智能化的简历批量投递。

### 核心优势

- ✅ **智能化** - AI 自动回答申请表单中的附加问题
- ✅ **高效率** - 批量投递，每小时可投递 50+ 职位
- ✅ **安全性** - 使用 undetected-chromedriver 避免被检测
- ✅ **可控性** - 支持黑名单、白名单、投递前暂停审核
- ✅ **可追踪** - 完整的投递历史记录和统计

## 🚀 快速开始

### 1. 访问自动投递面板

```
http://localhost:8000/static/auto_apply_panel.html
```

或在主界面点击"自动投递"标签页。

### 2. 配置投递参数

#### 基础配置

- **投递平台**：选择 LinkedIn（Boss直聘开发中）
- **投递数量**：建议每次 50 个以内（避免被封号）
- **搜索关键词**：例如 "Python Developer", "Full Stack Engineer"
- **工作地点**：例如 "Remote", "San Francisco", "北京"

#### 高级配置

- **公司黑名单**：不想投递的公司，每行一个
- **提交前暂停**：勾选后每次提交前会暂停，等待人工审核

### 3. 启动投递

点击"启动自动投递"按钮，系统会：

1. 验证配置有效性
2. 初始化浏览器（自动登录或使用已保存的会话）
3. 搜索符合条件的职位
4. 逐个投递，实时显示进度
5. 完成后生成统计报告

### 4. 实时监控

投递过程中可以看到：

- **进度条** - 当前投递进度
- **统计数字** - 成功/失败/总数/成功率
- **当前职位** - 正在投递的职位信息
- **实时日志** - 详细的操作日志

### 5. 停止投递

如需中途停止，点击"停止投递"按钮。

## ⚙️ 配置说明

### 用户资料配置

为了让 AI 更好地回答问题，建议在配置中提供以下信息：

```json
{
  "user_profile": {
    "email": "your@email.com",
    "password": "your_password",
    "work_authorization": "Yes",
    "salary_expectation": "100000",
    "years_of_experience": "5",
    "availability": "Immediately",
    "willing_to_relocate": "Yes",
    "education_level": "Bachelor's Degree",
    "language_proficiency": "Fluent"
  }
}
```

### 平台特定配置

#### LinkedIn

- **Easy Apply Only** - 只投递支持 Easy Apply 的职位
- **会话持久化** - 自动保存登录状态，下次无需重新登录
- **智能问答** - AI 自动回答表单中的附加问题

## 🔐 安全与合规

### 重要提示

⚠️ **使用前请阅读**

1. 自动投递功能仅供学习交流使用
2. 使用前请确保符合目标平台的服务条款
3. 过度使用可能导致账号被限制
4. 建议每日投递不超过 50 个职位
5. 本项目不对账号安全负责

### 安全措施

- ✅ **反检测** - 使用 undetected-chromedriver
- ✅ **随机延迟** - 模拟人类行为，避免被识别为机器人
- ✅ **会话管理** - 不存储明文密码，使用 Cookie 持久化
- ✅ **频率限制** - 默认限制每次最多 200 个职位

### 最佳实践

1. **首次使用** - 建议先投递 5-10 个职位测试
2. **投递频率** - 每天不超过 50 个职位
3. **黑名单** - 添加不感兴趣的公司到黑名单
4. **人工审核** - 重要职位建议开启"提交前暂停"
5. **定期检查** - 查看投递历史，分析成功率

## 📊 投递历史

### 查看历史记录

在"投递历史"面板可以看到：

- 投递时间
- 使用平台
- 投递状态（运行中/已完成/失败）
- 成功/总数统计

### 导出数据

点击"导出"按钮可以将投递历史导出为 CSV 文件。

## 🐛 常见问题

### Q1: 登录失败怎么办？

**A:**
1. 检查邮箱和密码是否正确
2. 如果需要验证码，会自动暂停等待人工输入
3. 建议首次使用时不要开启无头模式，方便处理验证

### Q2: 投递失败率很高？

**A:**
1. 检查是否被平台限制（登录查看是否有警告）
2. 降低投递频率，增加随机延迟
3. 检查简历是否完整（有些职位要求上传简历）

### Q3: 如何提高投递成功率？

**A:**
1. 完善用户资料配置，让 AI 更准确地回答问题
2. 使用关键词精准搜索，避免不匹配的职位
3. 添加黑名单，过滤不感兴趣的公司
4. 定期更新简历，保持竞争力

### Q4: 支持哪些平台？

**A:**
- ✅ LinkedIn（已支持）
- 🚧 Boss直聘（开发中）
- 🚧 智联招聘（计划中）
- 🚧 前程无忧（计划中）

### Q5: 会不会被封号？

**A:**
- 使用反检测技术，降低风险
- 遵循平台规则，控制投递频率
- 建议每日不超过 50 个职位
- 如果被限制，停止使用 24-48 小时

## 🔧 高级功能

### 自定义问题答案

编辑 `app/services/auto_apply/question_handler.py` 中的 `preset_answers` 字典，添加自定义问题答案。

### 多账号管理

通过 `user_id` 参数可以管理多个账号的会话：

```python
session_manager.save_cookies(driver, user_id="account1")
session_manager.load_cookies(driver, user_id="account1")
```

### API 调用

也可以通过 API 直接调用：

```bash
# 启动投递
curl -X POST http://localhost:8000/api/auto-apply/start \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "linkedin",
    "max_count": 50,
    "keywords": "Python Developer",
    "location": "Remote"
  }'

# 查询状态
curl http://localhost:8000/api/auto-apply/status/{task_id}

# 停止投递
curl -X POST http://localhost:8000/api/auto-apply/stop \
  -H "Content-Type: application/json" \
  -d '{"task_id": "xxx"}'
```

## 🙏 致谢

本功能整合自以下开源项目：

- [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn) - LinkedIn 自动投递核心逻辑
- [wodsuz/EasyApplyJobsBot](https://github.com/wodsuz/EasyApplyJobsBot) - 多平台投递参考

感谢开源社区的贡献！

## 📞 获取帮助

如果遇到问题：

1. 查看 [常见问题](#常见问题)
2. 查看 [GitHub Issues](https://github.com/emptyteabot/ai-job-helper/issues)
3. 加入 [讨论区](https://github.com/emptyteabot/ai-job-helper/discussions)

---

**祝您求职顺利！** 🎉
