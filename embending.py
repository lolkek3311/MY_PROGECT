import requests

# Используем модель OpenRouter (размерность будет 1536!)
OPENROUTER_API_KEY = "YOUR_API_KEY_FOR_OPENROUTER"
API_URL = "https://openrouter.ai/api/v1/embeddings"

def get_embedding(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost"
    }
    
    # Используем модель text-embedding-3-small (она дешевая/бесплатная и хорошая)
    payload = {
        "model": "openai/text-embedding-3-small",
        "input": text.replace("\n", " ")
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['data'][0]['embedding'] # Возвращает вектор 1536
    except Exception as e:
        print(f"Ошибка API: {e}")
        return []