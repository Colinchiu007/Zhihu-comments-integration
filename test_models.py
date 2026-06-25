import requests

models = ['agnes-20-flash', 'agnes-20', 'agnes-flash', 'agnes', 'gpt-3.5-turbo', 'gpt-4']

for model in models:
    try:
        r = requests.post('https://apihub.agnes-ai.com/v1/chat/completions',
            headers={'Content-Type':'application/json','Authorization':'Bearer sk-HWzfr2ZRBaSKeoseR9aLhx7AANOh4b96vVLQF8IwLoRYJJe8'},
            json={'model': model, 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 50},
            timeout=30)
        print(f'{model}: {r.status_code} - {r.text[:100]}')
    except Exception as e:
        print(f'{model}: Error - {str(e)[:50]}')