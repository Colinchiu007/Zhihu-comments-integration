"""评论改写器 - 生成可发表的完整文章"""
import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RewriteConfig:
    """改写配置"""
    max_words: int = 2000
    strategy: str = 'auto'
    focus_threshold: int = 20
    max_duplicate_ratio: float = 0.5
    use_llm: bool = False
    output_type: str = 'article'


class CommentRewriter:
    """评论改写器"""
    
    def __init__(self, config: Optional[RewriteConfig] = None):
        self.config = config or RewriteConfig()
    
    def _clean_html(self, text: str) -> str:
        if not text:
            return ''
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_opinions(self, comments: List[Dict[str, Any]]) -> List[str]:
        """提取评论观点，清理格式并添加标点"""
        opinions = []
        for comment in comments:
            content = self._clean_html(comment.get('content', ''))
            if content and len(content) > 10:
                # 确保有标点结尾
                if not content.endswith(('。', '！', '？', '...', '…')):
                    content = content + '。'
                opinions.append(content)
        return opinions[:10]
    
    def _generate_article(self, original: str, comments: List[Dict[str, Any]], 
                         analysis: Dict[str, Any]) -> str:
        """生成完整文章"""
        title = analysis.get('title', '话题讨论')
        original_clean = self._clean_html(original) if original else ''
        opinions = self._extract_opinions(comments)
        
        # 构建文章
        article = []
        
        # 开头：引入话题
        if original_clean:
            intro = self._create_intro(original_clean, title)
            article.append(intro)
        else:
            article.append(f'最近，关于"{title}"的话题在网上引发了热议。')
        
        article.append('')
        
        # 主体：网友观点整合
        if opinions:
            transitions = [
                '网友们对此议论纷纷：',
                '大家怎么看呢？',
                '评论区也炸开了锅：',
                '来看看大家怎么说：'
            ]
            article.append(random.choice(transitions))
            article.append('')
            
            for i, opinion in enumerate(opinions):
                article.append(f'{opinion}')
                article.append('')
        
        # 补充：从原文提取更多内容
        if original_clean and len(original_clean) > 300:
            # 提取原文后半部分
            second_half = original_clean[200:500]
            if second_half:
                article.append('此外，原文还提到：')
                article.append('')
                article.append(second_half + '。' if not second_half.endswith('。') else second_half)
                article.append('')
        
        # 结尾：总结
        article.append(f'关于这个话题，大家看法不一，这也正常。')
        article.append('')
        article.append('你怎么看？欢迎在评论区留言讨论。')
        
        return '\n'.join(article)
    
    def _create_intro(self, original: str, title: str) -> str:
        """创建文章开头"""
        # 提取原文核心句子
        sentences = re.split(r'[。！？]', original)
        
        # 找到有价值的句子
        good_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 150:
                good_sentences.append(sentence)
            if len(good_sentences) >= 3:
                break
        
        if good_sentences:
            return '。'.join(good_sentences) + '。'
        else:
            return f'最近，关于"{title}"的话题在网上引发了热议。'
    
    def _generate_koubao(self, original: str, comments: List[Dict[str, Any]], 
                        analysis: Dict[str, Any]) -> str:
        """生成口播文案"""
        title = analysis.get('title', '话题讨论')
        original_clean = self._clean_html(original) if original else ''
        opinions = self._extract_opinions(comments)
        
        article = []
        
        # 开场
        article.append(f'大家好，今天咱们聊聊"{title}"这个话题。')
        article.append('')
        
        # 引入
        if original_clean:
            intro = self._create_intro(original_clean, title)
            article.append(intro)
        article.append('')
        
        # 网友观点
        if opinions:
            article.append('来看看网友们怎么说：')
            article.append('')
            
            for opinion in opinions[:5]:
                article.append(f'"{opinion}"')
                article.append('')
        
        # 结尾
        article.append('总的来说，这个话题确实引发了大家的思考。')
        article.append('你怎么看？欢迎在评论区告诉我。')
        article.append('')
        article.append('记得点赞关注，我们下期再见！')
        
        return '\n'.join(article)
    
    def rewrite(self, original: str, comments: List[Dict[str, Any]], 
                analysis: Dict[str, Any]) -> str:
        """生成改写文案"""
        if self.config.use_llm:
            try:
                from llm.llm_client import LLMClient
                client = LLMClient()
                if client.is_available():
                    original_clean = self._clean_html(original)
                    return client.rewrite_article(
                        original_clean, comments,
                        max_words=self.config.max_words,
                        max_duplicate_ratio=self.config.max_duplicate_ratio
                    )
            except Exception as e:
                print(f'LLM调用失败，使用模板改写: {e}')
        
        if self.config.output_type == '口播':
            result = self._generate_koubao(original, comments, analysis)
        else:
            result = self._generate_article(original, comments, analysis)
        
        if len(result) > self.config.max_words:
            result = result[:self.config.max_words - 50] + '\n\n...（内容已截断）'
        
        return result