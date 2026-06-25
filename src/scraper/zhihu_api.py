import requests
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


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
            return {
                'type': 'answer',
                'question_id': answer_match.group(1),
                'answer_id': answer_match.group(2)
            }
        
        article_match = re.search(r'zhuanlan\.zhihu\.com/p/(\d+)', url)
        if article_match:
            return {'type': 'article', 'article_id': article_match.group(1)}
        
        return {'type': 'unknown'}
    
    def get_answer_detail(self, answer_id: str) -> Optional[Dict[str, Any]]:
        """获取回答详情（包含原文）"""
        api_url = f'https://www.zhihu.com/api/v4/answers/{answer_id}'
        params = {'include': 'content,voteup_count,comment_count,created_time,updated_time'}
        
        try:
            r = requests.get(api_url, headers=self.headers, params=params, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                return {
                    'answer_id': answer_id,
                    'question_id': str(data.get('question', {}).get('id', '')),
                    'question_title': data.get('question', {}).get('title', ''),
                    'author': data.get('author', {}).get('name', '匿名用户'),
                    'author_url': data.get('author', {}).get('url', ''),
                    'content': data.get('content', ''),
                    'excerpt': data.get('excerpt', ''),
                    'voteup_count': data.get('voteup_count', 0),
                    'comment_count': data.get('comment_count', 0),
                    'created_time': data.get('created_time', 0),
                    'updated_time': data.get('updated_time', 0),
                    'url': f'https://www.zhihu.com/question/{data.get("question", {}).get("id", "")}/answer/{answer_id}'
                }
            else:
                print(f'获取回答详情失败: {r.status_code}')
                return None
        except Exception as e:
            print(f'获取回答详情异常: {e}')
            return None
    
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
                content = item.get('content', '')
                # 清理HTML标签
                import re
                content_clean = re.sub(r'<.*?>', '', content).strip()
                
                comment = {
                    'comment_id': item.get('id', ''),
                    'author': item.get('author', {}).get('name', '匿名用户'),
                    'author_url': item.get('author', {}).get('url', ''),
                    'content': content,
                    'content_clean': content_clean,
                    'likes': item.get('vote_count', 0),
                    'created_time': item.get('created_time', 0),
                    'reply_count': item.get('reply_count', 0),
                    'sentiment': self._analyze_sentiment(content_clean)
                }
                all_comments.append(comment)
            
            offset += limit
            
            paging = result.get('paging', {})
            if paging.get('is_end', True):
                break
        
        return all_comments[:max_comments]
    
    def _analyze_sentiment(self, text: str) -> float:
        """分析文本情感（简单规则）"""
        if not text:
            return 0.5
        
        # 简单的正面/负面关键词
        positive_words = ['支持', '赞同', '好', '棒', '优秀', '点赞', '认同', '理解']
        negative_words = ['反对', '不支持', '批评', '质疑', '问题', '不好', '错']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 0.7
        elif negative_count > positive_count:
            return 0.3
        else:
            return 0.5
    
    def scrape(self, url: str, max_comments: int = 100, include_original: bool = False) -> Dict[str, Any]:
        """
        抓取知乎内容
        
        Args:
            url: 知乎链接
            max_comments: 最大评论数
            include_original: 是否包含原文
            
        Returns:
            包含原文和评论的字典
        """
        url_info = self.parse_url(url)
        result = {
            'url': url,
            'url_type': url_info['type'],
            'original': None,
            'comments': [],
            'scraped_at': datetime.now().isoformat()
        }
        
        if url_info['type'] == 'answer':
            answer_id = url_info['answer_id']
            
            # 获取原文
            if include_original:
                result['original'] = self.get_answer_detail(answer_id)
            
            # 获取评论
            result['comments'] = self.get_all_comments(answer_id, max_comments)
            result['answer_id'] = answer_id
            result['question_id'] = url_info['question_id']
            
        else:
            print(f'暂不支持URL类型: {url_info["type"]}')
        
        return result

if __name__ == '__main__':
    api = ZhihuAPI()
    url = 'https://www.zhihu.com/question/2002867368548923300/answer/2016406108428853709'
    
    print(f'抓取: {url}')
    comments = api.scrape(url, max_comments=20)
    
    print(f'\n共 {len(comments)} 条评论:')
    for i, c in enumerate(comments, 1):
        print(f'{i}. [{c["author"]}] {c["content"][:60]}')
