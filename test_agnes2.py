import requests

# 尝试不同的API端点
endpoints = [
    'https://api.agnes-ai.com/v1/chat/completions',
    'https://api.agnes-ai.com/v1/completions',
    'https://api.agnes-ai.com/chat/completions',
    'https://api.agnes-ai.com/completions',
    'https://agnes-ai.com/api/v1/chat/completions',
    'https://agnes-ai.com/api/chat/completions',
]

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk-HWzfr2ZRBaSKeoseR9aLhx7AANOh4b96vVLQF8IwLoRYJJe8'
}

data = {
    'model': 'agnes-20-flash',
    'messages': [{'role': 'user', 'content': 'hi'}],
    'max_tokens': 50
}

for endpoint in endpoints:
    try:
        r = requests.post(endpoint, headers=headers, json=data, timeout=10)
        print(f'{endpoint}: {r.status_code} - {r.text[:100]}')
    except Exception as e:
        print(f'{endpoint}: Error - {str(e)[:50]}')