# 智联招聘自动投递器

## ✨ 特性

- 🚀 **极速投递** - 使用 DrissionPage，速度比 Selenium 快 10 倍
- 🎯 **智能过滤** - 支持公司黑名单、关键词过滤、薪资筛选
- 💾 **会话保持** - 自动保存登录状态，7天内免登录
- 📊 **详细日志** - 完整记录投递过程和结果
- 🔧 **易于配置** - 简单的配置文件，快速上手

## 🚀 快速开始

### 1. 安装依赖

```bash
# 方式一：使用批处理脚本（Windows）
启动智联投递.bat

# 方式二：手动安装
pip install DrissionPage>=4.0.0
pip install -r requirements.txt
```

### 2. 运行测试

```bash
python test_zhilian.py
```

### 3. 基础使用

```python
from app.services.auto_apply.zhilian_applier import ZhilianApplier

# 创建投递器
config = {
    'blacklist_companies': ['外包', '劳务派遣'],
    'blacklist_keywords': ['实习', '兼职'],
    'min_salary': 8000
}
applier = ZhilianApplier(config)

# 登录
applier.login('your_phone', 'your_password')

# 搜索职位
jobs = applier.search_jobs(
    keywords='Python开发',
    location='北京',
    filters={'salary_range': '10001-15000'}
)

# 批量投递
results = applier.batch_apply(jobs, max_count=10)
print(f"成功: {results['applied']}, 失败: {results['failed']}")

# 清理
applier.cleanup()
```

## 📖 详细文档

查看完整使用指南：[智联招聘投递器使用指南](docs/智联招聘投递器使用指南.md)

## 🔧 配置说明

### 黑名单配置

```python
config = {
    # 不投递的公司
    'blacklist_companies': [
        '外包', '劳务派遣', '人力资源',
        '猎头', '中介', '培训'
    ],

    # 不投递的职位关键词
    'blacklist_keywords': [
        '实习', '兼职', '外包', '派遣',
        '销售', '客服', '电话'
    ],

    # 薪资范围（元/月）
    'min_salary': 8000,
    'max_salary': 30000
}
```

### 搜索过滤

```python
filters = {
    'salary_range': '10001-15000',  # 薪资范围
    'work_experience': '1-3年',     # 工作经验
    'education': '本科',            # 学历要求
}
```

## 📊 性能指标

- ✅ 登录成功率: >= 95%
- ✅ 搜索准确率: >= 99%
- ✅ 投递成功率: >= 90%
- ✅ 单次投递速度: < 10秒

## ⚠️ 注意事项

1. **登录验证码** - 首次登录可能需要手动处理验证码
2. **投递频率** - 建议每次投递间隔 3-5 秒，每天不超过 50 个
3. **账号安全** - 建议使用小号测试
4. **Cookie 有效期** - 7天，过期后需要重新登录

## 🛠️ 技术栈

- **DrissionPage** - 国产高速浏览器自动化框架
- **Python 3.8+** - 编程语言
- **PyPDF2** - 简历处理

## 📝 项目结构

```
app/services/auto_apply/
├── base_applier.py          # 基础投递类
├── zhilian_applier.py       # 智联招聘投递器 ⭐
├── linkedin_applier.py      # LinkedIn 投递器
├── session_manager.py       # 会话管理器
└── config.py                # 配置管理

test_zhilian.py              # 测试脚本
启动智联投递.bat              # 快速启动脚本
docs/智联招聘投递器使用指南.md # 详细文档
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**⚡ 使用 DrissionPage 驱动，速度快 10 倍！**
