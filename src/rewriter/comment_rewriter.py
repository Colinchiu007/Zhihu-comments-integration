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
        """清理HTML标签和特殊字符"""
        if not text:
            return ''
        # 移除HTML标签
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # 移除表情符号和特殊字符
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
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
            if not content or len(content) < 5:
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
    
    def _calculate_duplicate_ratio(self, text1: str, text2: str) -> float:
        """计算两段文本的重复率"""
        if not text1 or not text2:
            return 0.0
        
        # 提取中文字符和词语
        def extract_tokens(text):
            chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
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
        """重写内容以降低与原文的重复率"""
        current_ratio = self._calculate_duplicate_ratio(content, original)
        
        if current_ratio <= target_ratio:
            return content
        
        # 如果重复率太高，保留前半部分，删除重复的后半部分
        lines = content.split('\n')
        result_lines = []
        char_count = 0
        
        for line in lines:
            if char_count + len(line) > self.config.max_words * 0.7:
                break
            result_lines.append(line)
            char_count += len(line) + 1
        
        return '\n'.join(result_lines)
    
    def _summarize_comments(self, comments: List[str], max_items: int = 3) -> str:
        """将多条评论整合成摘要"""
        if not comments:
            return ''
        
        # 取最重要的几条
        selected = comments[:max_items]
        
        # 整合成连贯的段落
        parts = []
        for i, comment in enumerate(selected):
            # 截取关键部分
            if len(comment) > 80:
                comment = comment[:80] + '...'
            parts.append(comment)
        
        return '；'.join(parts)
    
    def _generate_rewrite(self, original: str, comments: List[Dict[str, Any]], 
                         analysis: Dict[str, Any], strategy: str) -> str:
        """生成改写文案"""
        key_points = self._extract_key_points(comments)
        comment_count = len(comments)
        
        # 获取标题（优先使用原文标题）
        title = analysis.get('title', '话题讨论')
        if not title or title == '话题讨论':
            # 从原文中提取标题
            original_clean = self._clean_html(original) if original else ''
            if original_clean:
                # 取第一句话作为标题
                first_sentence = re.split(r'[。！？]', original_clean)[0]
                if len(first_sentence) > 5 and len(first_sentence) < 50:
                    title = first_sentence
        
        summary = analysis.get('summary', '')
        
        # 清理原文
        original_clean = self._clean_html(original) if original else ''
        
        # 构建文章
        lines = []
        
        # 标题
        lines.append(f'# {title}')
        lines.append('')
        
        # 引言
        lines.append('## 引言')
        lines.append('')
        if original_clean:
            # 提取原文核心观点（前150字作为摘要）
            intro = original_clean[:150] + '...' if len(original_clean) > 150 else original_clean
            lines.append(intro)
        else:
            lines.append(f'近期，关于"{title}"的讨论引发了广泛关注。')
        lines.append('')
        
        # 主体：网友评论分析
        lines.append('## 网友观点分析')
        lines.append('')
        
        if strategy == '评论为主':
            # 以评论为主
            if key_points['positive']:
                lines.append('**积极观点：**')
                lines.append('')
                for point in key_points['positive'][:3]:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['negative']:
                lines.append('**质疑声音：**')
                lines.append('')
                for point in key_points['negative'][:3]:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['neutral']:
                lines.append('**中立观点：**')
                lines.append('')
                for point in key_points['neutral'][:2]:
                    lines.append(f'- {point}')
                lines.append('')
        
        elif strategy == '原文为主':
            # 以原文为主，但跳过引言部分（前150字）
            if original_clean and len(original_clean) > 150:
                # 从第150字开始，找到下一个完整的句子开头
                remaining = original_clean[150:]
                
                # 找到第一个完整句子的开头
                sentence_starters = ['而', '但', '然而', '同时', '另一方面', '此外', '另外']
                found_start = False
                
                for starter in sentence_starters:
                    idx = remaining.find(starter)
                    if idx >= 0 and idx < 50:
                        remaining = remaining[idx:]
                        found_start = True
                        break
                
                if not found_start:
                    # 如果没找到连接词，找第一个句号后的位置
                    for i, char in enumerate(remaining):
                        if char in '。！？' and i > 0:
                            remaining = remaining[i+1:]
                            break
                
                if remaining.strip():
                    lines.append(remaining.strip())
                    lines.append('')
            
            if comments:
                lines.append('**网友评论精选：**')
                lines.append('')
                for comment in comments[:5]:
                    content = self._clean_html(comment.get('content', ''))
                    if content and len(content) > 10:
                        lines.append(f'> {content}')
                        lines.append('')
        
        else:  # 均衡
            if original_clean:
                intro_len = min(150, len(original_clean) // 2)
                lines.append(original_clean[:intro_len] + '...')
                lines.append('')
            
            if key_points['positive']:
                lines.append('**正面声音：**')
                for point in key_points['positive'][:2]:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['negative']:
                lines.append('**反面思考：**')
                for point in key_points['negative'][:2]:
                    lines.append(f'- {point}')
                lines.append('')
        
        # 总结
        lines.append('## 总结')
        lines.append('')
        if summary:
            lines.append(summary)
        else:
            lines.append('该话题引发了广泛讨论，网友们从不同角度表达了自己的看法。')
        lines.append('')
        
        # 字数控制
        result = '\n'.join(lines)
        
        # 如果超长，精简内容
        if len(result) > self.config.max_words:
            result = self._trim_content(lines, self.config.max_words)
        
        return result
    
    def _trim_content(self, lines: List[str], max_words: int) -> str:
        """精简内容到指定字数"""
        result = '\n'.join(lines)
        
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