import aiohttp
import asyncio
import re
from config import AI_TOKEN

OPENROUTER_API_KEY = AI_TOKEN
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ⚡ БЫСТРАЯ МОДЕЛЬ
FAST_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"

# 🐢 УГЛУБЛЕННЫЕ МОДЕЛИ
DEEP_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]

# Запасные быстрые модели
BACKUP_FAST_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "openai/gpt-oss-20b:free",
]


async def generate(text: str, fast: bool = True) -> str:
    """fast=True - быстрый ответ, fast=False - углубленный ответ"""
    
    models = [FAST_MODEL] + BACKUP_FAST_MODELS if fast else DEEP_MODELS
    
    for model in models:
        result = await try_generate(text, model, fast)
        if result and not result.startswith("❌") and not result.startswith("⏰"):
            return result
    
    return "❌ Все модели временно недоступны. Попробуйте позже."


async def try_generate(text: str, model: str, fast: bool) -> str:
    """Пробует сгенерировать ответ через указанную модель"""
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
    }
    
    timeout = aiohttp.ClientTimeout(total=15 if fast else 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout) as response:
                
                if response.status == 429:
                    print(f"⚠️ Модель {model} rate-limited")
                    return ""
                
                if response.status != 200:
                    print(f"Ошибка API {model}: {response.status}")
                    return ""
                
                result = await response.json()
                answer = result['choices'][0]['message'].get('content', '')
                
                if answer:
                    # Очистка HTML
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
                
    except asyncio.TimeoutError:
        return "⏰ Сервер не отвечает. Попробуйте ещё раз."
    except Exception as e:
        print(f"Generate error: {e}")
        return ""
