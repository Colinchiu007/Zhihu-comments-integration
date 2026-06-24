import requests
import re

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

# 检查引号类型
print('Has ASCII quote:', '"' in reasoning)
print('Has Unicode quote:', '\u201c' in reasoning)

# 尝试不同的正则表达式
patterns = [
    r'"([^"]*[\u4e00-\u9fff][^"]*)"',
    r'\u201c([^\u201d]*[\u4e00-\u9fff][^\u201d]*)\u201d',
    r'[""]([^"]*[\u4e00-\u9fff][^"]*)[""]'
]

for pattern in patterns:
    quotes = re.findall(pattern, reasoning)
    print(f'Pattern {pattern[:20]}... found {len(quotes)} matches')
    if quotes:
        print(f'  Longest: {max(quotes, key=len)[:100]}')