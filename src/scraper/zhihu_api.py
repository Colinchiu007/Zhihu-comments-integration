import requests
import json
import re
from pathlib import Path
from typing import List, Dict, Any

class ZhihuAPI:
    def __init__(self, cookie_file: str = 'config/cookie.txt'):
        self.cookie = self._load_cookie(cookie_file)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cookie': self.cookie,
            'Referer': 'https://www.zhihu.com/'
        }
    
    def _load_cookie(self, cookie_file: str) -> str:
        path = Path(cookie_file)
        if path.exists():
            return path.read_text(encoding='utf-8').strip()
        return ''
    
    def parse_url(self, url: str) -> Dict[str, Any]:
        answer_match = re.search(r'zhihu\.com/question/(\d+)/answer/(\d+)', url)
        if answer_match:
            return {'type': 'answer', 'question_id': answer_match.group(1), 'answer_id': answer_match.group(2)}
        
        article_match = re.search(r'zhuanlan\.zhihu\.com/p/(\d+)', url)
        if article_match:
            return {'type': 'article', 'article_id': article_match.group(1)}
        
        return {'type': 'unknown'}
    
    def get_answer_comments(self, answer_id: str, limit: int = 20, offset: int = 0) -> Dict:
        api_url = f'https://www.zhihu.com/api/v4/answers/{answer_id}/comments'
        params = {'limit': limit, 'offset': offset, 'order': 'normal'}
        
        r = requests.get(api_url, headers=self.headers, params=params, timeout=15)
        
        if r.status_code == 200:
            return r.json()
        else:
            print(f'API错误: {r.status_code} {r.text[:100]}')
            return {'data': [], 'paging': {}}
    
    def get_all_comments(self, answer_id: str, max_comments: int = 100) -> List[Dict[str, Any]]:
        all_comments = []
        offset = 0
        limit = 20
        
        while len(all_comments) < max_comments:
            result = self.get_answer_comments(answer_id, limit=limit, offset=offset)
            
            data = result.get('data', [])
            if not data:
                break
            
            for item in data:
                comment = {
                    'author': item.get('author', {}).get('name', '匿名用户'),
                    'content': item.get('content', ''),
                    'likes': item.get('vote_count', 0),
                    'time': item.get('created_time', 0),
                    'reply_count': item.get('reply_count', 0)
                }
                all_comments.append(comment)
            
            offset += limit
            
            paging = result.get('paging', {})
            if paging.get('is_end', True):
                break
        
        return all_comments[:max_comments]
    
    def scrape(self, url: str, max_comments: int = 100) -> List[Dict[str, Any]]:
        url_info = self.parse_url(url)
        
        if url_info['type'] == 'answer':
            return self.get_all_comments(url_info['answer_id'], max_comments)
        else:
            print(f'暂不支持URL类型: {url_info["type"]}')
            return []

if __name__ == '__main__':
    api = ZhihuAPI()
    url = 'https://www.zhihu.com/question/2002867368548923300/answer/2016406108428853709'
    
    print(f'抓取: {url}')
    comments = api.scrape(url, max_comments=20)
    
    print(f'\n共 {len(comments)} 条评论:')
    for i, c in enumerate(comments, 1):
        print(f'{i}. [{c["author"]}] {c["content"][:60]}')
