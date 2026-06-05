import requests
import json
import asyncio
import re
from config import AI_TOKEN

OPENROUTER_API_KEY = f'sk{AI_TOKEN}'
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# РАБОЧАЯ БЕСПЛАТНАЯ МОДЕЛЬ С REASONING
FREE_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


async def generate(text: str) -> str:
    """Генерация ответа через OpenRouter с поддержкой reasoning"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    # Первый запрос с reasoning
    payload = {
        "model": FREE_MODEL,
        "messages": [
            {"role": "user", "content": text}
        ],
        "reasoning": {"enabled": True}
    }

    try:
        # Шаг 1: отправляем запрос
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            data=json.dumps(payload),  # используем data=json.dumps()
            timeout=60
        )

        if response.status_code != 200:
            print(f"OpenRouter error {response.status_code}: {response.text}")
            return "❌ Сервис временно недоступен. Попробуйте позже."

        result = response.json()
        assistant_msg = result['choices'][0]['message']
        first_answer = assistant_msg.get('content', '')

        # Если ответ пустой или это модерация
        if not first_answer or first_answer == "User Safety: safe":
            # Пробуем без reasoning
            payload["reasoning"] = {"enabled": False}
            response2 = requests.post(
                OPENROUTER_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            if response2.status_code == 200:
                first_answer = response2.json()['choices'][0]['message'].get('content', '')

        # Очистка от markdown
        if first_answer:
            first_answer = re.sub(r'\*\*?', '', first_answer)
            first_answer = re.sub(r'`{1,3}', '', first_answer)
            first_answer = re.sub(r'^#{1,6}\s+', '', first_answer, flags=re.MULTILINE)

        return first_answer.strip() if first_answer and first_answer.strip() else "✅ Готово!"

    except requests.exceptions.Timeout:
        return "⏰ Сервер не отвечает. Попробуйте ещё раз."
    except Exception as e:
        print(f"Generate error: {e}")
        return "❌ Ошибка соединения. Попробуйте позже."


