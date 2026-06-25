import requests

# 尝试其他可能的API地址
urls = [
    'https://api.agnes.ai/v1/chat/completions',
    'https://agnes.ai/api/v1/chat/completions',
    'https://api.agnes.ai/chat/completions',
    'https://agnes.ai/chat/completions',
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

for url in urls:
    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        print(f'{url}: {r.status_code} - {r.text[:100]}')
    except Exception as e:
        print(f'{url}: Error - {str(e)[:50]}')