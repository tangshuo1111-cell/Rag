import logging
from typing import Any, Dict

import httpx

from app.core.config import get_settings

logger = logging.getLogger("llm")
settings = get_settings()


async def call_deepseek_chat(question: str, context: str) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置，无法调用 DeepSeek 接口")

    system_prompt = (
        "你是一个企业知识库问答助手，只能根据提供的上下文回答问题。"
        "如果上下文中没有足够信息，请明确说明不知道，不要编造。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"上下文：\n{context}\n\n问题：{question}"},
    ]

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.2,
    }

    base = settings.deepseek_base_url.rstrip("/")

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("DeepSeek HTTP 错误 status=%s body=%s", resp.status_code, resp.text)
            raise RuntimeError(f"DeepSeek 调用失败：HTTP {resp.status_code}") from e

        data = resp.json()

    return data["choices"][0]["message"]["content"]