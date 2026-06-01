import requests


async def generate(text: str):
    """Максимально простой вариант"""

    try:
        url = f"https://text.pollinations.ai/{text}"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            return response.text
        else:
            return "❌ Сервис временно недоступен"
    except:
        return "❌ Ошибка. Попробуйте позже."
