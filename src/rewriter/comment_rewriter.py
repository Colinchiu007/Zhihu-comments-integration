"""评论改写器 - 生成可发表的文章或口播文案"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RewriteConfig:
    """改写配置"""
    max_words: int = 2000  # 最大字数
    strategy: str = 'auto'  # 改写策略: auto/评论为主/原文为主/均衡
    focus_threshold: int = 20  # 评论数阈值
    max_duplicate_ratio: float = 0.5  # 与原文最大重复率
    use_llm: bool = False  # 是否使用LLM改写
    output_type: str = 'article'  # 输出类型: article/口播


class CommentRewriter:
    """评论改写器"""
    
    def __init__(self, config: Optional[RewriteConfig] = None):
        self.config = config or RewriteConfig()
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签和特殊字符"""
        if not text:
            return ''
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_key_points(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取评论核心观点"""
        positive = []
        negative = []
        neutral = []
        
        for comment in comments:
            content = self._clean_html(comment.get('content', ''))
            if not content or len(content) < 10:
                continue
            
            # 精简评论，只保留核心观点
            if len(content) > 100:
                content = content[:100] + '...'
            
            # 使用评论自带的情感标签
            sentiment = comment.get('sentiment', 0.5)
            
            if sentiment > 0.6:
                positive.append(content)
            elif sentiment < 0.4:
                negative.append(content)
            else:
                neutral.append(content)
        
        return {
            'positive': positive[:5],
            'negative': negative[:5],
            'neutral': neutral[:3]
        }
    
    def _generate_article(self, original: str, comments: List[Dict[str, Any]], 
                         analysis: Dict[str, Any]) -> str:
        """生成完整文章"""
        key_points = self._extract_key_points(comments)
        title = analysis.get('title', '话题讨论')
        original_clean = self._clean_html(original) if original else ''
        
        # 文章结构
        article = []
        
        # 1. 标题
        article.append(f'# {title}')
        article.append('')
        
        # 2. 开头（引入话题）
        article.append('## 开头')
        article.append('')
        if original_clean:
            # 提取原文核心，用自己的话重新表述
            intro = self._rewrite_intro(original_clean, title)
            article.append(intro)
        else:
            article.append(f'最近，"{title}"这个话题在网上引发了热议。')
        article.append('')
        
        # 3. 主体（网友评论整理）
        article.append('## 网友怎么说')
        article.append('')
        
        if key_points['positive']:
            article.append('**支持的声音：**')
            article.append('')
            for point in key_points['positive']:
                article.append(f'- {point}')
            article.append('')
        
        if key_points['negative']:
            article.append('**反对的声音：**')
            article.append('')
            for point in key_points['negative']:
                article.append(f'- {point}')
            article.append('')
        
        if key_points['neutral']:
            article.append('**中立的看法：**')
            article.append('')
            for point in key_points['neutral']:
                article.append(f'- {point}')
            article.append('')
        
        # 4. 总结
        article.append('## 总结')
        article.append('')
        article.append(f'关于"{title}"，网友们众说纷纭。')
        if key_points['positive'] and key_points['negative']:
            article.append('有人支持，有人反对，这很正常。')
        elif key_points['positive']:
            article.append('总体来看，多数网友持支持态度。')
        elif key_points['negative']:
            article.append('总体来看，质疑的声音更多一些。')
        article.append('')
        article.append('你怎么看？欢迎在评论区留言讨论。')
        
        return '\n'.join(article)
    
    def _rewrite_intro(self, original: str, title: str) -> str:
        """重写开头，用自己的话表述"""
        # 提取原文核心观点
        sentences = re.split(r'[。！？]', original)
        
        # 找到最有价值的句子
        key_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 100:
                key_sentences.append(sentence)
            if len(key_sentences) >= 2:
                break
        
        if key_sentences:
            # 重新组织语言
            intro = '。'.join(key_sentences) + '。'
            return intro
        else:
            return f'最近，关于"{title}"的话题在网上引发了广泛讨论。'
    
    def _generate_koubao(self, original: str, comments: List[Dict[str, Any]], 
                        analysis: Dict[str, Any]) -> str:
        """生成口播文案"""
        key_points = self._extract_key_points(comments)
        title = analysis.get('title', '话题讨论')
        original_clean = self._clean_html(original) if original else ''
        
        article = []
        
        # 开场
        article.append(f'大家好，今天咱们聊聊"{title}"这个话题。')
        article.append('')
        
        # 引入
        if original_clean:
            intro = self._rewrite_intro(original_clean, title)
            article.append(intro)
        article.append('')
        
        # 网友观点
        article.append('来看看网友们怎么说：')
        article.append('')
        
        if key_points['positive']:
            article.append('有网友表示支持：')
            for point in key_points['positive'][:2]:
                article.append(f'"{point}"')
            article.append('')
        
        if key_points['negative']:
            article.append('也有网友提出质疑：')
            for point in key_points['negative'][:2]:
                article.append(f'"{point}"')
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
        # 如果配置使用LLM，优先使用LLM
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
        
        # 根据输出类型生成
        if self.config.output_type == '口播':
            result = self._generate_koubao(original, comments, analysis)
        else:
            result = self._generate_article(original, comments, analysis)
        
        # 字数控制
        if len(result) > self.config.max_words:
            result = result[:self.config.max_words - 50] + '\n\n...（内容已截断）'
        
        return result