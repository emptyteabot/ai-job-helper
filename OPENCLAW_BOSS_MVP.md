# 本机 MVP：AI 分析后自动输出 Boss 直聘岗位链接（手动投递）

## 这是什么

这是一个本机可用的求职助手 MVP：

1. 你上传/粘贴简历
2. 后端调用 DeepSeek 做 6 角色协作分析（职业分析、岗位建议、简历优化、面试准备等）
3. **分析完成后，自动用你的简历信息生成搜索词**
4. 通过 **OpenClaw 控制你已登录的 Chrome（Boss 直聘）**，自动打开搜索页并抓取岗位详情链接
5. 前端展示一组 `job_detail` 链接，你点击后 **手动投递**

为什么是“手动投递”：
- 国内招聘网站通常有验证码/风控/条款限制，云端或无人值守的“自动提交投递”不稳定且高风险
- MVP 目标是：**把“找链接”自动化**，把“投递点击”留给你

## 适用范围

- ✅ 本机（Windows）可用
- ✅ 需要你已登录 Boss 直聘的浏览器会话
- ❌ 不适合部署到云端给所有用户共享（OpenClaw 依赖你的本机浏览器与登录态）

## 前置条件

1. Python 依赖已安装
   - `pip install -r requirements.txt`
2. `.env` 里配置 DeepSeek Key
   - `DEEPSEEK_API_KEY=...`
3. 选择本机 OpenClaw 数据源
   - `JOB_DATA_PROVIDER=openclaw`
   - 可选：只启用 Boss（默认就是 Boss）
     - `OPENCLAW_JOB_SITES=boss`

## 启动步骤（从 0 到可用）

1. 启动后端
```powershell
cd "$env:USERPROFILE\\Desktop\\自动投简历"
python web_app.py
```

2. 打开 Web
- `http://localhost:8000/app`

3. 连接 OpenClaw（关键一步，只要 attach 过就能用）
1. 打开 Chrome 并进入 Boss 直聘任意页面
2. 点击浏览器右上角 **OpenClaw 扩展图标**，选择 **Attach/连接** 当前标签页

## 使用方式（你每次怎么用）

1. 在 `http://localhost:8000/app` 上传 PDF/Word/TXT 或粘贴简历
2. 点击 `🚀 开始AI分析`
3. 等结果出来后：
   - 页面底部会自动填好“关键词/城市”
   - **如果 `JOB_DATA_PROVIDER=openclaw`，会自动触发一次 Boss 搜索**
   - 你会看到“实时岗位搜索（Boss直聘）”的进度条在跑
4. 搜索完成后返回岗位列表
   - 点 `投递（跳转）` 打开岗位详情页
   - 你在页面里手动点投递

## 你会看到浏览器“自己动”的原因

当启用 `openclaw` 数据源时，后端会执行：
- `openclaw browser navigate ...`
- `openclaw browser evaluate ...`

它会驱动你 attach 的那个标签页跳转/读取链接，所以你会看到浏览器自己跳页面，这是正常行为。

## 故障排查

1. 搜索按钮点了没反应 / 报“no tab is connected”
- 说明 OpenClaw 没 attach 到任何标签页
- 重新在 Boss 页面点击 OpenClaw 扩展图标 Attach

2. 返回岗位为 0
- 可能 Boss 页面还没加载完，等几秒再搜一次
- 或者当前页面被风控拦截，手动刷新 Boss 搜索页后再试

3. AI 分析报错
- 基本是 `DEEPSEEK_API_KEY` 未配置/无效
- 访问 `http://localhost:8000/api/health` 看服务是否正常

## 云端部署怎么处理

云端可以部署“AI 分析”本身，但不要启用 `openclaw`：
- 云端不要设置 `JOB_DATA_PROVIDER=openclaw`
- OpenClaw 只在你的本机有效

