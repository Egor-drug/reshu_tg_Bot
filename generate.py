import requests
import json
import asyncio
import re
from config import AI_TOKEN

OPENROUTER_API_KEY = AI_TOKEN
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ⚡ БЫСТРАЯ МОДЕЛЬ
FAST_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"

# 🐢 УГЛУБЛЕННЫЕ МОДЕЛИ (качественные)
DEEP_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",  # Супер (качественная)
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",# Ультра (ваша старая)
]

# Запасные быстрые модели (на случай rate-limit)
BACKUP_FAST_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "openai/gpt-oss-20b:free",
]


async def generate(text: str, fast: bool = True) -> str:
    """
    fast=True - быстрый ответ (nemotron-nano-12b)
    fast=False - углубленный ответ (пробует super, потом ultra)
    """

    if fast:
        # Быстрый режим
        result = await try_generate_with_model(text, FAST_MODEL, fast=True)

        if not result or result.startswith("❌") or result.startswith("⏰"):
            print(f"🔄 Быстрая модель недоступна, пробуем запасные...")
            for backup_model in BACKUP_FAST_MODELS:
                result = await try_generate_with_model(text, backup_model, fast=True)
                if result and not result.startswith("❌") and not result.startswith("⏰"):
                    return result
            return "❌ Все быстрые модели временно недоступны. Попробуйте углубленный режим."
        return result
    else:
        # Углубленный режим - пробуем модели по очереди
        for deep_model in DEEP_MODELS:
            result = await try_generate_with_model(text, deep_model, fast=False)
            if result and not result.startswith("❌") and not result.startswith("⏰"):
                return result
        return "❌ Все углубленные модели временно недоступны. Попробуйте быстрый режим."


async def try_generate_with_model(text: str, model: str, fast: bool) -> str:
    """Пробует сгенерировать ответ через указанную модель"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
    }

    try:
        loop = asyncio.get_event_loop()
        timeout = 15 if fast else 30

        response = await loop.run_in_executor(
            None,
            lambda: requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
        )

        if response.status_code == 429:
            print(f"⚠️ Модель {model} rate-limited")
            return ""

        if response.status_code != 200:
            print(f"Ошибка API {model}: {response.status_code}")
            return ""

        result = response.json()
        answer = result['choices'][0]['message'].get('content', '')

        if answer:
            # Очистка HTML тегов
            answer = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'\n**\1**\n', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<b>(.*?)</b>', r'**\1**', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<strong>(.*?)</strong>', r'**\1**', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<i>(.*?)</i>', r'*\1*', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<em>(.*?)</em>', r'*\1*', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<br\s*/?>', '\n', answer, flags=re.IGNORECASE)
            answer = re.sub(r'<p>(.*?)</p>', r'\1\n', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<[^>]+>', '', answer)
            answer = re.sub(r'\n{3,}', '\n\n', answer)

        return answer.strip() if answer else ""

    except requests.exceptions.Timeout:
        return "⏰ Сервер не отвечает. Попробуйте ещё раз."
    except Exception as e:
        print(f"Generate error with {model}: {e}")
        return ""
