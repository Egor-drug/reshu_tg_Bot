import requests
import re

async def generate(text: str):
    """Генерация ответа с очисткой от таблиц и лишнего форматирования"""

    try:
        url = f"https://text.pollinations.ai/{text}"
        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            answer = response.text
            
            # Удаляем markdown символы
            answer = answer.replace('**', '')
            answer = answer.replace('*', '')
            answer = answer.replace('`', '')
            
            # Удаляем строки с таблицами (содержат | и ---)
            lines = answer.split('\n')
            clean_lines = []
            for line in lines:
                # Пропускаем строки с символами таблиц
                if '|' in line and '---' in line:
                    continue
                if line.strip() == '---':
                    continue
                # Убираем оставшиеся |
                line = line.replace('|', '')
                # Убираем лишние пробелы
                line = re.sub(r'\s+', ' ', line).strip()
                if line:
                    clean_lines.append(line)
            
            answer = '\n'.join(clean_lines)
            
            # Если после очистки ничего не осталось, вернуть оригинал без **
            if len(answer) < 10:
                answer = response.text.replace('**', '').replace('|', '')
            
            return answer
        else:
            return "❌ Сервис временно недоступен"
    except Exception as e:
        print(f"Error: {e}")
        return "❌ Ошибка. Попробуйте позже."
