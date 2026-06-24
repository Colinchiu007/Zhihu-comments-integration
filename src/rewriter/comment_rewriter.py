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


class CommentRewriter:
    """评论改写器"""
    
    def __init__(self, config: Optional[RewriteConfig] = None):
        self.config = config or RewriteConfig()
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()
    
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
        
        # 开头
        title = analysis.get('title', '话题讨论')
        summary = analysis.get('summary', '')
        
        lines = []
        lines.append(f'# {title} - 深度解读')
        lines.append('')
        
        # 原文摘要
        if original:
            lines.append('## 原文概述')
            lines.append('')
            original_clean = self._clean_html(original)
            if len(original_clean) > 500:
                original_clean = original_clean[:500] + '...'
            lines.append(original_clean)
            lines.append('')
        
        # 根据策略生成正文
        if strategy == '评论为主':
            lines.append('## 网友热议')
            lines.append('')
            lines.append(f'该话题共收到 **{comment_count}** 条评论，以下是网友们的主要观点：')
            lines.append('')
            
            if key_points['positive']:
                lines.append('### 正面观点')
                lines.append('')
                for point in key_points['positive']:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['negative']:
                lines.append('### 质疑声音')
                lines.append('')
                for point in key_points['negative']:
                    lines.append(f'- {point}')
                lines.append('')
            
            if key_points['themes']:
                lines.append('### 热议话题')
                lines.append('')
                lines.append('、'.join(key_points['themes']))
                lines.append('')
        
        elif strategy == '原文为主':
            lines.append('## 内容解读')
            lines.append('')
            
            if original:
                original_clean = self._clean_html(original)
                lines.append(original_clean)
                lines.append('')
            
            if comments:
                lines.append('## 评论区精选')
                lines.append('')
                for comment in comments[:10]:
                    content = self._clean_html(comment.get('content', ''))
                    if content:
                        lines.append(f'> {content}')
                        lines.append('')
        
        else:  # 均衡
            lines.append('## 内容概要')
            lines.append('')
            if original:
                original_clean = self._clean_html(original)
                if len(original_clean) > 300:
                    original_clean = original_clean[:300] + '...'
                lines.append(original_clean)
            lines.append('')
            
            lines.append('## 网友观点')
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
        
        # 总结
        lines.append('## 总结')
        lines.append('')
        lines.append(summary if summary else '该话题引发了广泛讨论，网友们从不同角度表达了自己的看法。')
        lines.append('')
        
        # 标注
        lines.append('---')
        lines.append(f'*本文基于{comment_count}条网友评论自动改写生成，仅供参考。*')
        
        return '\n'.join(lines)
    
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
        comment_count = len(comments)
        strategy = self._determine_strategy(comment_count)
        
        result = self._generate_rewrite(original, comments, analysis, strategy)
        
        # 字数控制
        if len(result) > self.config.max_words:
            result = result[:self.config.max_words - 20] + '\n\n...(内容已截断)'
        
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
