"""评论改写器 - 结合原文和评论生成改写文案"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RewriteConfig:
    """改写配置"""
    max_words: int = 2000  # 最大字数
    strategy: str = 'auto'  # 改写策略: auto/评论为主/原文为主/均衡
    focus_threshold: int = 20  # 评论数阈值，低于此值时以原文为主
    max_duplicate_ratio: float = 0.5  # 与原文最大重复率（0-1）
    use_llm: bool = False  # 是否使用LLM改写


class CommentRewriter:
    """评论改写器"""
    
    def __init__(self, config: Optional[RewriteConfig] = None):
        self.config = config or RewriteConfig()
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()
    
    def _calculate_duplicate_ratio(self, text1: str, text2: str) -> float:
        """
        计算两段文本的重复率
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            重复率（0-1）
        """
        if not text1 or not text2:
            return 0.0
        
        # 提取中文字符和词语
        def extract_tokens(text):
            # 提取中文字符
            chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
            # 提取2-4字词语
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
            return set(chinese_chars + words)
        
        tokens1 = extract_tokens(text1)
        tokens2 = extract_tokens(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # 计算交集
        intersection = tokens1.intersection(tokens2)
        
        # 重复率 = 交集大小 / 较小集合大小
        min_size = min(len(tokens1), len(tokens2))
        if min_size == 0:
            return 0.0
        
        return len(intersection) / min_size
    
    def _rewrite_to_reduce_duplicate(self, content: str, original: str, 
                                    target_ratio: float) -> str:
        """
        重写内容以降低与原文的重复率
        
        Args:
            content: 当前内容
            original: 原文
            target_ratio: 目标重复率
            
        Returns:
            重写后的内容
        """
        current_ratio = self._calculate_duplicate_ratio(content, original)
        
        if current_ratio <= target_ratio:
            return content
        
        # 提取原文的关键信息
        original_tokens = set(re.findall(r'[\u4e00-\u9fa5]{2,}', original))
        
        # 提取内容中的重复部分
        content_tokens = set(re.findall(r'[\u4e00-\u9fa5]{2,}', content))
        duplicate_tokens = content_tokens.intersection(original_tokens)
        
        # 替换策略：删除部分重复内容，添加评论观点
        rewritten = content
        
        # 删除部分重复的句子
        sentences = re.split(r'[。！？]', original)
        for sentence in sentences:
            if len(sentence) > 5 and sentence in rewritten:
                # 只保留句子的前几个字
                shortened = sentence[:3] + '...'
                rewritten = rewritten.replace(sentence, shortened, 1)
        
        return rewritten
    
    def _determine_strategy(self, comment_count: int) -> str:
        """根据评论数量确定改写策略"""
        if self.config.strategy != 'auto':
            return self.config.strategy
        
        if comment_count >= self.config.focus_threshold:
            return '评论为主'
        else:
            return '原文为主'
    
    def _extract_key_points(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取评论关键点"""
        if not comments:
            return {'positive': [], 'negative': [], 'neutral': [], 'themes': []}
        
        positive = []
        negative = []
        neutral = []
        
        for comment in comments:
            content = self._clean_html(comment.get('content', ''))
            if not content:
                continue
                
            sentiment = comment.get('sentiment', 0.5)
            
            if sentiment > 0.6:
                positive.append(content)
            elif sentiment < 0.4:
                negative.append(content)
            else:
                neutral.append(content)
        
        # 提取主题词
        all_content = ' '.join([self._clean_html(c.get('content', '')) for c in comments])
        themes = self._extract_themes(all_content)
        
        return {
            'positive': positive[:5],
            'negative': negative[:5],
            'neutral': neutral[:3],
            'themes': themes
        }
    
    def _extract_themes(self, text: str) -> List[str]:
        """提取主题词"""
        try:
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(text, topK=5, withWeight=False)
            return keywords
        except:
            return []
    
    def _generate_rewrite(self, original: str, comments: List[Dict[str, Any]], 
                         analysis: Dict[str, Any], strategy: str) -> str:
        """生成改写文案"""
        key_points = self._extract_key_points(comments)
        comment_count = len(comments)
        
        # 获取标题
        title = analysis.get('title', '话题讨论')
        summary = analysis.get('summary', '')
        
        # 根据策略生成正文
        lines = []
        
        if strategy == '评论为主':
            lines.append(f'## {title}')
            lines.append('')
            
            if key_points['positive']:
                lines.append('多数网友对此持肯定态度：')
                lines.append('')
                for point in key_points['positive']:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['negative']:
                lines.append('也有部分网友提出不同看法：')
                lines.append('')
                for point in key_points['negative']:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['themes']:
                lines.append(f'讨论主要围绕{"、".join(key_points["themes"])}展开。')
                lines.append('')
        
        elif strategy == '原文为主':
            lines.append(f'## {title}')
            lines.append('')
            
            if original:
                original_clean = self._clean_html(original)
                # 控制与原文的重复率
                if len(original_clean) > 200:
                    # 只取部分内容，降低重复率
                    original_clean = original_clean[:200] + '...'
                lines.append(original_clean)
                lines.append('')
            
            if comments:
                lines.append('---')
                lines.append('')
                lines.append('**网友评论精选：**')
                lines.append('')
                for comment in comments[:10]:
                    content = self._clean_html(comment.get('content', ''))
                    if content:
                        lines.append(f'> {content}')
                        lines.append('')
        
        else:  # 均衡
            lines.append(f'## {title}')
            lines.append('')
            
            if original:
                original_clean = self._clean_html(original)
                # 控制与原文的重复率，最多取150字
                if len(original_clean) > 150:
                    original_clean = original_clean[:150] + '...'
                lines.append(original_clean)
                lines.append('')
            
            if key_points['positive']:
                lines.append('**赞同的声音：**')
                for point in key_points['positive'][:3]:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['negative']:
                lines.append('**反对的声音：**')
                for point in key_points['negative'][:3]:
                    lines.append(f'- {point}')
                lines.append('')
        
        # 字数控制 - 在生成时就控制，不截断
        result = '\n'.join(lines)
        
        # 如果超长，精简内容
        if len(result) > self.config.max_words:
            result = self._trim_content(lines, self.config.max_words)
        
        return result
    
    def _trim_content(self, lines: List[str], max_words: int) -> str:
        """精简内容到指定字数"""
        result = '\n'.join(lines)
        
        # 如果还是超长，逐步精简
        if len(result) > max_words:
            # 保留标题和前半部分
            trimmed_lines = []
            current_len = 0
            
            for line in lines:
                if current_len + len(line) + 1 > max_words - 50:
                    break
                trimmed_lines.append(line)
                current_len += len(line) + 1
            
            result = '\n'.join(trimmed_lines)
        
        return result
    
    def rewrite(self, original: str, comments: List[Dict[str, Any]], 
                analysis: Dict[str, Any]) -> str:
        """
        生成改写文案
        
        Args:
            original: 原文内容
            comments: 评论列表
            analysis: 分析结果
            
        Returns:
            改写后的文案
        """
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
        
        # 使用模板改写
        comment_count = len(comments)
        strategy = self._determine_strategy(comment_count)
        
        result = self._generate_rewrite(original, comments, analysis, strategy)
        
        # 检查与原文的重复率
        if original and self.config.max_duplicate_ratio < 1.0:
            original_clean = self._clean_html(original)
            current_ratio = self._calculate_duplicate_ratio(result, original_clean)
            
            # 如果重复率超过限制，进行重写
            if current_ratio > self.config.max_duplicate_ratio:
                result = self._rewrite_to_reduce_duplicate(
                    result, original_clean, self.config.max_duplicate_ratio
                )
        
        return result


if __name__ == '__main__':
    # 测试
    config = RewriteConfig(max_words=1000, strategy='auto')
    rewriter = CommentRewriter(config)
    
    original = "这是一篇关于人工智能发展的文章..."
    comments = [
        {'content': '写得很好，人工智能确实是未来趋势', 'sentiment': 0.8},
        {'content': '但是AI也带来了很多问题', 'sentiment': 0.3},
        {'content': '中立看待，技术本身无罪', 'sentiment': 0.5}
    ]
    analysis = {
        'title': '人工智能发展',
        'summary': '共3条评论，整体情感中立'
    }
    
    result = rewriter.rewrite(original, comments, analysis)
    print(result)
