"""单元测试"""
import pytest
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scraper.zhihu_api import ZhihuAPI
from analyzer.comment_analyzer import CommentAnalyzer
from generator.article_generator import ArticleGenerator


class TestZhihuAPI:
    def test_parse_url_answer(self):
        api = ZhihuAPI()
        url = "https://www.zhihu.com/question/123456/answer/789012"
        result = api.parse_url(url)
        assert result['type'] == 'answer'
        assert result['answer_id'] == '789012'
    
    def test_parse_url_article(self):
        api = ZhihuAPI()
        url = "https://zhuanlan.zhihu.com/p/123456789"
        result = api.parse_url(url)
        assert result['type'] == 'article'
        assert result['article_id'] == '123456789'


class TestCommentAnalyzer:
    def test_clean_html(self):
        analyzer = CommentAnalyzer()
        html = "<p>测试文本</p>"
        result = analyzer._clean_html(html)
        assert result == '测试文本'
    
    def test_analyze(self):
        analyzer = CommentAnalyzer()
        comments = [
            {"content": "很好的文章", "likes": "10"},
            {"content": "不认同观点", "likes": "5"}
        ]
        result = analyzer.analyze(comments)
        assert 'stats' in result
        assert result['stats']['total_comments'] == 2


class TestArticleGenerator:
    def test_generate(self):
        generator = ArticleGenerator()
        analysis = {
            'stats': {'total_comments': 1, 'avg_sentiment': 0.7, 'positive_ratio': 0.6, 'negative_ratio': 0.3,
                     'keywords': ['测试'], 'word_freq': [('测试', 1)], 'sentiments': [0.7]},
            'comments': [{'content': '测试', 'sentiment': 0.7}],
            'positive_comments': [],
            'negative_comments': [],
            'summary': '测试摘要'
        }
        result = generator.generate(analysis)
        assert '测试摘要' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])