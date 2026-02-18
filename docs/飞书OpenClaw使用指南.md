# 飞书 + OpenClaw 投递方案

## 概述

使用你的飞书机器人 + OpenClaw 实现自动投递，完全闭环。

## 配置信息

**你的飞书机器人：**
- App ID: `cli_a908b88dc6b8dcd4`
- App Secret: `Q8jjY7RDcwfcsmTd0Zvylee4dfs6kVhK`

## 工作流程

```
Streamlit 网页
    ↓
AI 分析简历 → 提取投递目标
    ↓
发送到飞书机器人
    ↓
飞书发送卡片消息（包含 OpenClaw 命令）
    ↓
你在电脑上运行 OpenClaw 命令
    ↓
OpenClaw 自动投递
    ↓
结果回传到飞书
    ↓
飞书通知你投递结果
```

## 安装 OpenClaw

### 方法1：npm 安装（推荐）

```bash
npm install -g openclaw
```

### 方法2：从源码安装

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
npm install
npm link
```

### 验证安装

```bash
openclaw --version
```

## 获取飞书用户 ID

### 方法1：通过飞书 API

1. 打开飞书开放平台：https://open.feishu.cn/
2. 进入你的应用
3. 权限管理 → 添加权限：`contact:user.id:readonly`
4. 使用 API 获取：

```bash
curl -X GET \
  'https://open.feishu.cn/open-apis/contact/v3/users/me' \
  -H 'Authorization: Bearer YOUR_USER_ACCESS_TOKEN'
```

### 方法2：通过飞书机器人

1. 在飞书中给机器人发消息
2. 机器人回复你的 `open_id`

### 方法3：使用邮箱（推荐）

直接使用你的飞书邮箱，系统会自动转换为 `open_id`。

## 使用步骤

### 1. 在网页上分析简历

1. 访问：https://your-app.streamlit.app
2. 上传简历或粘贴文本
3. 点击「开始分析」
4. 等待 AI 分析完成

### 2. 发送投递任务到飞书

1. 切换到「一键投递」标签
2. 选择「飞书 + OpenClaw」
3. 输入你的飞书用户 ID（或邮箱）
4. 选择投递平台（Boss直聘/实习僧/牛客网）
5. 点击「发送到飞书」

### 3. 在飞书中查看任务

你会收到一条卡片消息，包含：
- 投递策略（关键词、地点、数量）
- OpenClaw 命令
- Selenium 脚本（备用）

### 4. 运行 OpenClaw 命令

复制飞书消息中的命令，在电脑上运行：

```bash
openclaw run \
  --site zhipin \
  --keywords "Python OR Django OR 后端" \
  --locations "北京,上海" \
  --max-count 30 \
  --interval 5 \
  --callback https://your-service.com/api/callback/abc123
```

### 5. 等待投递完成

OpenClaw 会：
- 自动打开浏览器
- 搜索匹配的岗位
- 自动投递
- 实时显示进度
- 完成后回传结果

### 6. 查看投递结果

飞书会收到完成通知，包含：
- 总投递数量
- 成功/失败数量
- 详细投递列表
- 下一步建议

## OpenClaw 命令详解

### 基本命令

```bash
openclaw run [options]
```

### 常用选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--site` | 投递平台 | `zhipin`, `shixiseng`, `nowcoder` |
| `--keywords` | 搜索关键词 | `"Python OR Django"` |
| `--locations` | 工作地点 | `"北京,上海,深圳"` |
| `--max-count` | 最大投递数 | `30` |
| `--interval` | 投递间隔（秒） | `5` |
| `--callback` | 回调 URL | `https://...` |
| `--headless` | 无头模式 | `true` |
| `--proxy` | 代理服务器 | `http://proxy:8080` |

### 示例命令

**Boss直聘投递：**
```bash
openclaw run \
  --site zhipin \
  --keywords "Python实习" \
  --locations "北京" \
  --max-count 20 \
  --interval 5
```

**实习僧投递：**
```bash
openclaw run \
  --site shixiseng \
  --keywords "后端开发" \
  --locations "上海,杭州" \
  --max-count 30
```

**牛客网投递：**
```bash
openclaw run \
  --site nowcoder \
  --keywords "算法工程师" \
  --locations "深圳" \
  --max-count 15
```

## 高级功能

### 1. 自动回传结果

添加 `--callback` 参数，OpenClaw 会自动回传结果到飞书：

```bash
openclaw run \
  --site zhipin \
  --keywords "Python" \
  --callback https://your-service.com/api/callback/task_123
```

### 2. 定时投递

使用 cron 定时执行：

```bash
# 每天早上 9 点投递
0 9 * * * openclaw run --site zhipin --keywords "Python" --max-count 30
```

### 3. 批量投递

创建配置文件 `apply_config.json`：

```json
{
  "tasks": [
    {
      "site": "zhipin",
      "keywords": "Python",
      "locations": ["北京", "上海"],
      "max_count": 30
    },
    {
      "site": "shixiseng",
      "keywords": "后端开发",
      "locations": ["杭州"],
      "max_count": 20
    }
  ]
}
```

运行：

```bash
openclaw batch --config apply_config.json
```

## 常见问题

### Q1: OpenClaw 是什么？

A: OpenClaw 是一个开源的浏览器自动化工具，专门用于招聘网站的自动投递。

### Q2: 需要一直盯着电脑吗？

A: 不需要。OpenClaw 会自动运行，你可以去做其他事情。建议首次使用时在旁边观察。

### Q3: 会不会被封号？

A: 只要遵循以下规则，风险很低：
- 每天投递 ≤ 30 个
- 间隔 5-10 秒
- 不要在深夜投递

### Q4: OpenClaw 支持哪些平台？

A: 目前支持：
- ✅ Boss直聘
- ✅ 实习僧
- ✅ 牛客网
- 🚧 智联招聘（开发中）
- 🚧 前程无忧（开发中）

### Q5: 如何查看投递进度？

A: OpenClaw 会实时输出进度：

```
[1/30] 正在投递：Python后端实习生 - 字节跳动
[2/30] 正在投递：Django开发实习 - 美团
...
```

### Q6: 投递失败怎么办？

A: OpenClaw 会自动重试 3 次。如果还是失败，会跳过该岗位继续投递。

### Q7: 可以自定义投递策略吗？

A: 可以。修改配置文件或命令行参数即可。

### Q8: 如何停止投递？

A: 按 `Ctrl+C` 即可停止。

## 技术支持

**遇到问题？**
- 📧 发送邮件到：support@example.com
- 💬 加入 QQ 群：123456789
- 📖 查看文档：https://docs.example.com
- 🐛 提交 Issue：https://github.com/your-repo/issues

## 更新日志

### v1.0.0 (2026-02-18)
- ✨ 首次发布
- 🤖 支持飞书机器人集成
- 🚀 支持 OpenClaw 自动投递
- 📊 支持结果回传

### 下一步计划
- 🔄 支持更多招聘平台
- 📈 添加数据统计功能
- 🎯 优化投递策略
- 🤖 AI 自动回复 HR
