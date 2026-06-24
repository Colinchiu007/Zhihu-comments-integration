"""单元测试"""
import pytest
import sys
import shutil
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scraper.zhihu_api import ZhihuAPI
from analyzer.comment_analyzer import CommentAnalyzer
from generator.article_generator import ArticleGenerator
from rewriter.comment_rewriter import CommentRewriter, RewriteConfig
from data.storage import DataStorage


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


class TestCommentRewriter:
    def test_config_default(self):
        config = RewriteConfig()
        assert config.max_words == 2000
        assert config.strategy == 'auto'
        assert config.focus_threshold == 20
    
    def test_determine_strategy(self):
        config = RewriteConfig(strategy='auto')
        rewriter = CommentRewriter(config)
        
        # 评论数少于阈值，应返回"原文为主"
        assert rewriter._determine_strategy(10) == '原文为主'
        
        # 评论数多于阈值，应返回"评论为主"
        assert rewriter._determine_strategy(30) == '评论为主'
    
    def test_rewrite(self):
        config = RewriteConfig(max_words=1000, strategy='评论为主')
        rewriter = CommentRewriter(config)
        
        original = "测试原文内容"
        comments = [
            {'content': '很好的观点', 'sentiment': 0.8},
            {'content': '有些不同意', 'sentiment': 0.3}
        ]
        analysis = {'title': '测试话题', 'summary': '测试摘要'}
        
        result = rewriter.rewrite(original, comments, analysis)
        assert '测试话题' in result
        assert '很好的观点' in result


class TestDataStorage:
    def setup_method(self):
        """测试前清理"""
        self.test_dir = Path('test_data_storage')
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def teardown_method(self):
        """测试后清理"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_save_and_load(self):
        storage = DataStorage(str(self.test_dir))
        
        test_data = {
            'question_id': '123456',
            'answer_id': '789012',
            'url': 'https://www.zhihu.com/question/123456/answer/789012',
            'original': {'content': '测试原文', 'author': '测试作者'},
            'comments': [
                {'author': '用户1', 'content': '评论1'},
                {'author': '用户2', 'content': '评论2'}
            ],
            'scraped_at': '2026-01-01T00:00:00'
        }
        
        # 保存
        file_path = storage.save_answer(test_data)
        assert Path(file_path).exists()
        
        # 加载
        loaded = storage.load_answer('123456', '789012')
        assert loaded is not None
        assert loaded['answer_id'] == '789012'
        assert len(loaded['comments']) == 2
    
    def test_list_answers(self):
        storage = DataStorage(str(self.test_dir))
        
        # 保存两个回答
        for i in range(2):
            test_data = {
                'question_id': '123456',
                'answer_id': f'78901{i}',
                'url': f'https://www.zhihu.com/question/123456/answer/78901{i}',
                'comments': [{'author': '用户', 'content': f'评论{i}'}],
                'scraped_at': '2026-01-01T00:00:00'
            }
            storage.save_answer(test_data)
        
        # 列出
        answers = storage.list_answers('123456')
        assert len(answers) == 2
    
    def test_statistics(self):
        storage = DataStorage(str(self.test_dir))
        
        test_data = {
            'question_id': '123456',
            'answer_id': '789012',
            'comments': [{'author': '用户', 'content': '评论'}] * 5,
            'scraped_at': '2026-01-01T00:00:00'
        }
        storage.save_answer(test_data)
        
        stats = storage.get_statistics()
        assert stats['total_answers'] == 1
        assert stats['total_comments'] == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])