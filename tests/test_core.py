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
from llm.config_manager import LLMConfigManager, LLMConfig


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
        assert config.max_duplicate_ratio == 0.5
    
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
    
    def test_rewrite_auto_strategy(self):
        """测试自动策略选择"""
        config = RewriteConfig(max_words=2000, strategy='auto')
        rewriter = CommentRewriter(config)
        
        # 评论少于20条，使用原文为主
        comments_short = [{'content': f'评论{i}', 'sentiment': 0.5} for i in range(10)]
        result = rewriter.rewrite('原文内容', comments_short, {'title': '测试'})
        assert '原文内容' in result
        
        # 评论多于20条，使用评论为主
        comments_long = [{'content': f'评论{i}', 'sentiment': 0.5} for i in range(25)]
        result = rewriter.rewrite('原文内容', comments_long, {'title': '测试'})
        assert '网友' in result or '评论' in result
    
    def test_clean_html(self):
        """测试HTML清理"""
        config = RewriteConfig()
        rewriter = CommentRewriter(config)
        
        html_content = '<p>这是一段<b>带HTML</b>的文本</p>'
        result = rewriter._clean_html(html_content)
        assert '<p>' not in result
        assert '<b>' not in result
        assert '这是一段带HTML的文本' in result
    
    def test_calculate_duplicate_ratio(self):
        """测试重复率计算"""
        config = RewriteConfig()
        rewriter = CommentRewriter(config)
        
        # 完全相同的文本
        text1 = "这是一段测试文本"
        text2 = "这是一段测试文本"
        ratio = rewriter._calculate_duplicate_ratio(text1, text2)
        assert ratio == 1.0
        
        # 完全不同的文本
        text1 = "这是第一段文本"
        text2 = "那是完全不同的内容"
        ratio = rewriter._calculate_duplicate_ratio(text1, text2)
        assert ratio < 0.3
        
        # 部分重复的文本
        text1 = "人工智能是未来趋势"
        text2 = "人工智能带来了很多问题"
        ratio = rewriter._calculate_duplicate_ratio(text1, text2)
        assert 0.2 < ratio < 0.8
    
    def test_rewrite_with_duplicate_control(self):
        """测试带重复率控制的改写"""
        config = RewriteConfig(max_words=1000, strategy='评论为主', max_duplicate_ratio=0.5)
        rewriter = CommentRewriter(config)
        
        original = "人工智能是未来发展趋势，将改变我们的生活方式"
        comments = [
            {'content': 'AI确实很重要', 'sentiment': 0.7},
            {'content': '但也带来了隐私问题', 'sentiment': 0.3}
        ]
        analysis = {'title': '人工智能讨论', 'summary': '讨论'}
        
        result = rewriter.rewrite(original, comments, analysis)
        
        # 检查结果包含评论内容
        assert 'AI' in result or '人工智能' in result
        # 检查结果不完全等于原文
        assert result != original


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


class TestLLMConfigManager:
    def test_config_save_and_load(self):
        """测试配置保存和加载"""
        import tempfile
        import shutil
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            manager = LLMConfigManager(str(temp_dir))
            
            # 创建测试配置
            config = LLMConfig(
                provider='test',
                base_url='https://test.com/v1',
                api_key='test-api-key-12345',
                model='test-model'
            )
            
            # 保存
            manager.save_config(config)
            
            # 加载
            loaded = manager.get_config()
            
            assert loaded.provider == 'test'
            assert loaded.base_url == 'https://test.com/v1'
            assert loaded.api_key == 'test-api-key-12345'
            assert loaded.model == 'test-model'
        finally:
            shutil.rmtree(temp_dir)
    
    def test_config_encryption(self):
        """测试配置加密"""
        import tempfile
        import shutil
        
        temp_dir = Path(tempfile.mkdtemp())
        try:
            manager = LLMConfigManager(str(temp_dir))
            
            # 创建测试配置
            config = LLMConfig(api_key='secret-api-key')
            manager.save_config(config)
            
            # 检查文件中的API Key是否加密
            config_file = temp_dir / 'llm_config.json'
            with open(config_file, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
            
            # API Key应该被加密，不是明文
            assert data['api_key'] != 'secret-api-key'
            assert data['api_key'] != ''
            
            # 加载后应该能解密
            loaded = manager.get_config()
            assert loaded.api_key == 'secret-api-key'
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])