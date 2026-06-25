import requests

models = ['agnes-1.5-flash', 'agnes-2.0-flash']

for model in models:
    try:
        r = requests.post('https://apihub.agnes-ai.com/v1/chat/completions',
            headers={'Content-Type':'application/json','Authorization':'Bearer sk-HWzfr2ZRBaSKeoseR9aLhx7AANOh4b96vVLQF8IwLoRYJJe8'},
            json={'model': model, 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 50},
            timeout=60)
        print(f'{model}: {r.status_code} - {r.text[:200]}')
    except Exception as e:
        print(f'{model}: Error - {str(e)[:100]}')