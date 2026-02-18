import os
import random
from typing import Dict

from openai import AsyncOpenAI, OpenAI


def _first_non_empty(*keys: str) -> str:
    for k in keys:
        v = os.getenv(k, "").strip()
        if v:
            return v
    return ""


def _get_api_key() -> str:
    """获取 API Key，支持多 Key 轮换"""
    # 检查是否有多个 Key
    keys_str = os.getenv("DEEPSEEK_API_KEYS", "").strip()
    if keys_str:
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        if keys:
            return random.choice(keys)

    # 单个 Key
    return _first_non_empty(
        "OPENAI_COMPAT_API_KEY",
        "LLM_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
    )


def _infer_provider(base_url: str) -> str:
    u = (base_url or "").lower()
    if "oneapi.gemiaude.com" in u:
        return "gemiaude-openai-compatible"
    if "cookcode.gemiaude.com" in u:
        return "gemiaude-anthropic-proxy"
    if "deepseek.com" in u:
        return "deepseek"
    return "custom"


def get_llm_settings() -> Dict[str, str]:
    api_key = _get_api_key()
    base_url = _first_non_empty(
        "OPENAI_COMPAT_BASE_URL",
        "LLM_BASE_URL",
        "DEEPSEEK_BASE_URL",
    ) or "https://api.deepseek.com"

    chat_model = _first_non_empty(
        "OPENAI_COMPAT_MODEL",
        "LLM_MODEL",
        "DEEPSEEK_MODEL",
    ) or "deepseek-chat"

    reasoning_model = _first_non_empty(
        "OPENAI_COMPAT_REASONING_MODEL",
        "LLM_REASONING_MODEL",
        "DEEPSEEK_REASONING_MODEL",
    )
    if not reasoning_model:
        if "deepseek" in base_url.lower():
            reasoning_model = "deepseek-reasoner"
        else:
            reasoning_model = chat_model

    timeout_s = int(os.getenv("LLM_TIMEOUT_S", "120") or "120")  # 推理模型需要更长时间
    return {
        "api_key": api_key,
        "base_url": base_url,
        "chat_model": chat_model,
        "reasoning_model": reasoning_model,
        "provider": _infer_provider(base_url),
        "timeout_s": timeout_s,
    }


def get_async_llm_client() -> AsyncOpenAI:
    s = get_llm_settings()
    return AsyncOpenAI(api_key=s["api_key"], base_url=s["base_url"], timeout=s["timeout_s"])


def get_sync_llm_client() -> OpenAI:
    s = get_llm_settings()
    return OpenAI(api_key=s["api_key"], base_url=s["base_url"], timeout=s["timeout_s"])


def get_public_llm_config() -> Dict[str, str]:
    s = get_llm_settings()
    return {
        "provider": s["provider"],
        "base_url": s["base_url"],
        "chat_model": s["chat_model"],
        "reasoning_model": s["reasoning_model"],
        "api_key_configured": bool(s["api_key"]),
    }
