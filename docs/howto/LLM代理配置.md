# LLM代理配置（OpenAI兼容）

## 目标
让项目使用中转 API（OpenAI 兼容消息格式），支持自定义 `base_url` + `model`。

## 推荐配置（开发）
在 `.env` 设置：

```env
OPENAI_COMPAT_BASE_URL=https://oneapi.gemiaude.com/v1
OPENAI_COMPAT_API_KEY=你的令牌
OPENAI_COMPAT_MODEL=claude-sonnet-4.5
# 可选：推理模型单独指定，不填则自动回退到 chat 模型
OPENAI_COMPAT_REASONING_MODEL=
```

## 已支持的环境变量优先级
`OPENAI_COMPAT_* > LLM_* > DEEPSEEK_*`

也就是说：
- 你填了 `OPENAI_COMPAT_*`，就会优先走中转。
- 不填时，自动回退到原来的 DeepSeek 配置。

## 接口验证
启动后访问：
- `/api/health`

查看：
- `config.llm.base_url`
- `config.llm.chat_model`
- `config.llm.reasoning_model`
- `config.llm.api_key_configured`

## 注意
- 不要把真实 key 提交到 Git 或发到聊天里。
- 如果 key 泄露，立刻在提供商后台重置。
