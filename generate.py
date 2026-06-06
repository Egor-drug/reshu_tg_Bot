import requests
import json
import asyncio
import re
from config import AI_TOKEN

OPENROUTER_API_KEY = AI_TOKEN
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


async def generate(text: str) -> str:
    """Генерация ответа через OpenRouter с правильным форматированием"""
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": FREE_MODEL, "messages": [{"role": "user", "content": text}], "reasoning": {"enabled": True}}
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60))
        
        if response.status_code != 200:
            return "❌ Сервис недоступен"
        
        answer = response.json()['choices'][0]['message'].get('content', '')
        
        if not answer or answer == "User Safety: safe":
            payload["reasoning"] = {"enabled": False}
            response = await loop.run_in_executor(None, lambda: requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60))
            if response.status_code == 200:
                answer = response.json()['choices'][0]['message'].get('content', '')
        
        if answer:
            # Заголовки → **жирный текст** + перенос
            answer = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'\n**\1**\n', answer, flags=re.IGNORECASE | re.DOTALL)
            
            # Жирный текст
            answer = re.sub(r'<b>(.*?)</b>', r'**\1**', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<strong>(.*?)</strong>', r'**\1**', answer, flags=re.IGNORECASE | re.DOTALL)
            
            # Курсив
            answer = re.sub(r'<i>(.*?)</i>', r'*\1*', answer, flags=re.IGNORECASE | re.DOTALL)
            answer = re.sub(r'<em>(.*?)</em>', r'*\1*', answer, flags=re.IGNORECASE | re.DOTALL)
            
            # Перенос строки для <br> и <p>
            answer = re.sub(r'<br\s*/?>', '\n', answer, flags=re.IGNORECASE)
            answer = re.sub(r'<p>(.*?)</p>', r'\1\n', answer, flags=re.IGNORECASE | re.DOTALL)
            
            # Удаляем все оставшиеся HTML теги
            answer = re.sub(r'<[^>]+>', '', answer)
            
            # Убираем лишние переносы
            answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        return answer.strip() if answer else "✅ Готово!"
        
    except Exception as e:
        return "❌ Ошибка"
