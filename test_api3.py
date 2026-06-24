import requests

r = requests.post(
    'https://token.sensenova.cn/v1/chat/completions',
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-pGcjHf5L9vnO45VfR9v5lAGqHhQNAihd'
    },
    json={
        'model': 'sensenova-6.7-flash-lite',
        'messages': [
            {'role': 'system', 'content': '直接输出'},
            {'role': 'user', 'content': '100字介绍AI'}
        ],
        'max_tokens': 500
    },
    timeout=30
)

reasoning = r.json()['choices'][0]['message'].get('reasoning', '')

# 打印reasoning中的特殊字符
print('Reasoning length:', len(reasoning))
print('First 500 chars:')
print(reasoning[:500])
print()
print('Last 500 chars:')
print(reasoning[-500:])