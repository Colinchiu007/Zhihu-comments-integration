import requests

# 测试不同的API地址
urls = [
    'https://api.agnes-ai.com/v1/chat/completions',
    'https://api.agnes-ai.com/chat/completions',
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
        print(f'{url}: {r.status_code} - {r.text[:200]}')
    except Exception as e:
        print(f'{url}: Error - {str(e)[:100]}')